"""
实例管理路由
"""

import json
from pathlib import Path
from typing import List

import pyjson5
from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Instance
from app.schemas import ApiResponse, InstanceConfig, InstanceCreate, InstanceResponse
from app.services.docker_service import DockerService
from app.services.instance_service import InstanceService

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

    # 创建实例
    service = InstanceService(db)
    try:
        instance = await service.create_instance(req.id, req.name)
        return ApiResponse(
            data={"instance": instance.to_dict()},
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
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    service = DockerService()
    try:
        await service.start_instance(instance_id)
        instance.status = "running"
        db.commit()
        return ApiResponse(message="实例启动成功")
    except Exception as e:
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


@router.get("/instances/{instance_id}/config", response_model=ApiResponse)
async def get_instance_config(instance_id: str, db: Session = Depends(get_db)):
    """获取实例配置（openclaw.json）"""
    instance = db.query(Instance).filter(Instance.id == instance_id).first()
    if not instance:
        raise HTTPException(status_code=404, detail="实例不存在")

    config_path = Path(f"../instances/{instance_id}/data/openclaw.json")
    if not config_path.exists():
        # 返回默认配置
        default_config = '''{
    // OpenClaw 网关配置
    "gateway": {
        "mode": "local",
        "token": "",
        "port": 18789
    },
    // 智能体配置
    "agents": {
        "defaults": {
            "model": "gpt-4",
            "sandbox": {
                "mode": "non-main",
                "scope": "agent"
            }
        }
    },
    // 渠道配置
    "channels": [],
    // 工具配置
    "tools": {
        "defaults": ["*"]
    }
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

    # 保存配置
    config_path = Path(f"../instances/{instance_id}/data/openclaw.json")
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
        await websocket.send_text(f"[ERROR] {e}")
    finally:
        await websocket.close()
