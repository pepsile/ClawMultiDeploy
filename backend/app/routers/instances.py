"""
实例管理路由
"""

import json
import logging
import secrets
from pathlib import Path
from typing import List

import pyjson5
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT, get_db
from app.models import Instance
from app.schemas import ApiResponse, DeviceApproveRequest, InstanceConfig, InstanceCreate, InstanceResponse
from app.services.docker_service import DockerService
from app.services.instance_service import InstanceService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/instances", response_model=ApiResponse)
async def get_instances(db: Session = Depends(get_db)):
    """获取所有实例列表"""
    instances = db.query(Instance).all()
    return ApiResponse(
        data={"instances": [inst.to_dict() for inst in instances]}
    )


@router.post("/instances", response_model=ApiResponse)
async def create_instance(
    req: InstanceCreate,
    db: Session = Depends(get_db)
):
    """创建新实例"""
    # 检查 ID 是否已存在
    if db.query(Instance).filter(Instance.id == req.id).first():
        raise HTTPException(status_code=400, detail=f"实例 ID '{req.id}' 已存在")

    # 创建实例（密码 + 自动生成 token 写入 gateway.auth，控制台需 token 做 API 鉴权）
    service = InstanceService(db)
    try:
        instance, gateway_token = await service.create_instance(req.id, req.name, req.password)
        return ApiResponse(
            data={
                "instance": instance.to_dict(),
                "gateway_token": gateway_token,
            },
            message="实例创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/instances/{instance_id}", response_model=ApiResponse)
async def get_instance(instance_id: str, db: Session = Depends(get_db)):
    """获取实例详情"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    return ApiResponse(data={"instance": instance.to_dict()})


@router.get("/instances/{instance_id}/gateway-token", response_model=ApiResponse)
async def get_instance_gateway_token(instance_id: str, db: Session = Depends(get_db)):
    """获取实例控制台令牌（用于拼带 token 的 URL，仅读 gateway.auth.token）"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    config_path, _ = _instance_config_path(instance_id)
    if not config_path.exists():
        return ApiResponse(data={"token": None})
    try:
        raw = config_path.read_text(encoding="utf-8")
        cfg = pyjson5.loads(raw)
        auth = (cfg.get("gateway") or {}).get("auth")
        token = auth.get("token") if isinstance(auth, dict) else None
        return ApiResponse(data={"token": token or None})
    except Exception:
        return ApiResponse(data={"token": None})


@router.post("/instances/{instance_id}/regenerate-gateway-token", response_model=ApiResponse)
async def regenerate_gateway_token(instance_id: str, db: Session = Depends(get_db)):
    """重新生成实例控制台令牌（写入 gateway.auth.token）。生效需重启实例。"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    config_path, _ = _instance_config_path(instance_id)
    if not config_path.exists():
        raise HTTPException(status_code=400, detail="实例配置文件不存在")
    try:
        raw = config_path.read_text(encoding="utf-8")
        cfg = pyjson5.loads(raw)
        gateway = cfg.get("gateway")
        if not isinstance(gateway, dict):
            gateway = {}
            cfg["gateway"] = gateway
        auth = gateway.get("auth")
        if not isinstance(auth, dict):
            auth = {}
            gateway["auth"] = auth
        new_token = secrets.token_urlsafe(24)
        auth["token"] = new_token
        config_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2), encoding="utf-8")
        return ApiResponse(
            data={"token": new_token, "port": instance.port},
            message="令牌已重新生成，请重启实例后使用新链接连接",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新生成令牌失败: {e}")


def _get_gateway_token_from_config(instance_id: str) -> str | None:
    """从实例 openclaw.json 读取 gateway.auth.token"""
    config_path, _ = _instance_config_path(instance_id)
    if not config_path.exists():
        return None
    try:
        raw = config_path.read_text(encoding="utf-8")
        cfg = pyjson5.loads(raw)
        auth = (cfg.get("gateway") or {}).get("auth")
        return auth.get("token") if isinstance(auth, dict) else None
    except Exception:
        return None


@router.get("/instances/{instance_id}/devices", response_model=ApiResponse)
async def list_instance_devices(instance_id: str, db: Session = Depends(get_db)):
    """获取实例设备配对列表（待批准 + 已配对），用于解决 pairing required"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    if instance.status != "running":
        raise HTTPException(status_code=400, detail="实例未运行，请先启动实例")
    token = _get_gateway_token_from_config(instance_id)
    if not token:
        raise HTTPException(status_code=400, detail="未配置 gateway.auth.token，请使用「重新生成令牌」或编辑配置")
    try:
        raw = await DockerService().devices_list(instance_id, token)
        data = json.loads(raw) if raw.strip() else {}
        return ApiResponse(data=data)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"解析 devices 输出失败: {e}")


@router.post("/instances/{instance_id}/devices/approve", response_model=ApiResponse)
async def approve_instance_device(
    instance_id: str,
    body: DeviceApproveRequest,
    db: Session = Depends(get_db),
):
    """批准一个待配对的设备，解决「pairing required」"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")
    if instance.status != "running":
        raise HTTPException(status_code=400, detail="实例未运行，请先启动实例")
    token = _get_gateway_token_from_config(instance_id)
    if not token:
        raise HTTPException(status_code=400, detail="未配置 gateway.auth.token，请使用「重新生成令牌」或编辑配置")
    try:
        await DockerService().devices_approve(instance_id, body.requestId, token)
        return ApiResponse(message="设备已批准")
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/instances/{instance_id}", response_model=ApiResponse)
async def delete_instance(
    instance_id: str,
    keep_data: bool = False,
    db: Session = Depends(get_db)
):
    """删除实例"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    service = InstanceService(db)
    try:
        await service.delete_instance(instance_id, keep_data)
        return ApiResponse(message="实例删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/start", response_model=ApiResponse)
async def start_instance(instance_id: str, db: Session = Depends(get_db)):
    """启动实例"""
    logger.info("POST /api/instances/%s/start 请求", instance_id)

    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        logger.warning("实例不存在: %s", instance_id)
        raise HTTPException(status_code=404, detail="实例不存在")

    # 启动前确保 docker-compose.yml 与当前实例列表一致
    instance_service = InstanceService(db)
    await instance_service._regenerate_compose()

    service = DockerService()
    try:
        await service.start_instance(instance_id)
        instance.status = "running"
        db.commit()
        logger.info("实例启动成功: %s", instance_id)
        return ApiResponse(message="实例启动成功")
    except Exception as e:
        logger.exception("启动实例失败 instance_id=%s: %s", instance_id, e)
        instance.status = "error"
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/stop", response_model=ApiResponse)
async def stop_instance(instance_id: str, db: Session = Depends(get_db)):
    """停止实例"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    service = DockerService()
    try:
        await service.stop_instance(instance_id)
        instance.status = "stopped"
        db.commit()
        return ApiResponse(message="实例停止成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/instances/{instance_id}/init", response_model=ApiResponse)
async def init_instance(instance_id: str, db: Session = Depends(get_db)):
    """初始化实例（运行 openclaw onboard）"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    service = DockerService()
    try:
        result = await service.init_instance(instance_id)
        return ApiResponse(data={"result": result}, message="初始化完成")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _instance_config_path(instance_id: str, prefer_data: bool = True) -> tuple[Path, Path]:
    """返回 (主路径, 回退路径)。官方用 /home/node/.openclaw → 对应 data，优先 data。"""
    base = PROJECT_ROOT / "instances" / instance_id
    data_path = base / "data" / "openclaw.json"
    config_path = base / "config" / "openclaw.json"
    if prefer_data and data_path.exists():
        return data_path, config_path
    if config_path.exists():
        return config_path, data_path
    return data_path, config_path  # 默认读写 data


@router.get("/instances/{instance_id}/config", response_model=ApiResponse)
async def get_instance_config(instance_id: str, db: Session = Depends(get_db)):
    """获取实例配置（openclaw.json）"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    config_path, _ = _instance_config_path(instance_id)
    if not config_path.exists():
        # 返回默认配置：使用 gateway.auth.token（已弃用 gateway.token），默认 bailian 模型，无 feishu
        default_config = '''{
  "meta": { "lastTouchedVersion": "2026.2.25" },
  "wizard": { "lastRunCommand": "onboard", "lastRunMode": "local" },
  "models": {
    "mode": "merge",
    "providers": {
      "bailian": {
        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
        "apiKey": "",
        "api": "openai-completions",
        "models": [
          { "id": "qwen3.5-plus", "name": "qwen3.5-plus", "api": "openai-completions", "reasoning": false, "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 65536 },
          { "id": "glm-5", "name": "glm-5", "api": "openai-completions", "reasoning": false, "input": ["text"], "contextWindow": 202752, "maxTokens": 16384 },
          { "id": "glm-4.7", "name": "glm-4.7", "api": "openai-completions", "reasoning": false, "input": ["text"], "contextWindow": 202752, "maxTokens": 16384 }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": { "primary": "bailian/glm-5" },
      "models": { "bailian/qwen3.5-plus": {}, "bailian/glm-5": {}, "bailian/glm-4.7": {} },
      "workspace": "/home/node/.openclaw/workspace",
      "compaction": { "mode": "safeguard" },
      "maxConcurrent": 4
    }
  },
  "gateway": {
    "port": 18789,
    "mode": "local",
    "bind": "lan",
    "controlUi": {
      "allowedOrigins": [ "http://127.0.0.1:18789", "http://localhost:18789" ]
    },
    "auth": { "mode": "token", "token": "", "password": "" }
  },
  "channels": {},
  "session": { "dmScope": "per-channel-peer" },
  "commands": { "native": "auto", "nativeSkills": "auto", "restart": true }
}'''
        return ApiResponse(data={"content": default_config})

    try:
        content = config_path.read_text(encoding="utf-8")
        return ApiResponse(data={"content": content})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取配置失败: {e}")


@router.put("/instances/{instance_id}/config", response_model=ApiResponse)
async def update_instance_config(
    instance_id: str,
    config: InstanceConfig,
    db: Session = Depends(get_db)
):
    """更新实例配置"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    # 验证 JSON5 语法
    try:
        pyjson5.loads(config.content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON5 格式错误: {e}")

    # 保存配置（写入 data，对应容器内 /home/node/.openclaw/openclaw.json）
    config_path = PROJECT_ROOT / "instances" / instance_id / "data" / "openclaw.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        config_path.write_text(config.content, encoding="utf-8")
        return ApiResponse(message="配置保存成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存配置失败: {e}")


@router.websocket("/instances/{instance_id}/logs")
async def instance_logs(websocket: WebSocket, instance_id: str):
    """WebSocket 实时日志"""
    await websocket.accept()

    service = DockerService()
    try:
        async for log_line in service.stream_logs(instance_id):
            await websocket.send_text(log_line)
    except Exception as e:
        # 连接可能已被前端关闭，此时再发送会触发 RuntimeError，这里静默忽略
        try:
            await websocket.send_text(f"[ERROR] {e}")
        except RuntimeError:
            pass
    finally:
        try:
            await websocket.close()
        except RuntimeError:
            pass
