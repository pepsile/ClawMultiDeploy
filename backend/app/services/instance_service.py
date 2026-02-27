"""
实例业务逻辑服务
"""

import asyncio
import json
import secrets
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.database import PROJECT_ROOT
from app.models import Instance


class InstanceService:
    """实例管理服务"""

    # 与官方 Gateway 端口一致：18789 / 18790，每实例占 2 个连续端口
    BASE_PORT = 18789

    def __init__(self, db: Session):
        self.db = db

    def _get_next_port(self) -> int:
        """获取下一个可用网关端口（宿主机）；每实例占用 port 与 port+1"""
        used = set()
        for i in self.db.query(Instance.port).all():
            used.add(i.port)
            used.add(i.port + 1)
        port = self.BASE_PORT
        while port in used or (port + 1) in used:
            port += 2
        return port

    async def create_instance(self, instance_id: str, name: str, password: str) -> tuple[Instance, str]:
        """创建新实例；password 与生成的 token 写入 gateway.auth（控制台需 token 做 API 鉴权）。返回 (instance, gateway_token)。"""
        # 分配端口
        port = self._get_next_port()
        gateway_token = secrets.token_urlsafe(24)

        # 目录结构对齐官方：data → /home/node/.openclaw，workspace 在其下
        base_path = PROJECT_ROOT / "instances" / instance_id
        (base_path / "data").mkdir(parents=True, exist_ok=True)
        (base_path / "data" / "workspace").mkdir(parents=True, exist_ok=True)

        # 默认配置写入 data/openclaw.json（容器内即 /home/node/.openclaw/openclaw.json）
        # 使用 gateway.auth.token（官方已弃用 gateway.token），默认模型为 bailian，不包含 feishu 等渠道
        config_path = base_path / "data" / "openclaw.json"
        default_config = {
            "meta": {
                "lastTouchedVersion": "2026.2.25",
                "lastTouchedAt": None,
            },
            "wizard": {
                "lastRunCommand": "onboard",
                "lastRunMode": "local",
            },
            "models": {
                "mode": "merge",
                "providers": {
                    "bailian": {
                        "baseUrl": "https://coding.dashscope.aliyuncs.com/v1",
                        "apiKey": "",
                        "api": "openai-completions",
                        "models": [
                            {"id": "qwen3.5-plus", "name": "qwen3.5-plus", "api": "openai-completions", "reasoning": False, "input": ["text", "image"], "contextWindow": 1000000, "maxTokens": 65536},
                            {"id": "glm-5", "name": "glm-5", "api": "openai-completions", "reasoning": False, "input": ["text"], "contextWindow": 202752, "maxTokens": 16384},
                            {"id": "glm-4.7", "name": "glm-4.7", "api": "openai-completions", "reasoning": False, "input": ["text"], "contextWindow": 202752, "maxTokens": 16384},
                        ],
                    }
                },
            },
            "agents": {
                "defaults": {
                    "model": {"primary": "bailian/glm-5"},
                    "models": {
                        "bailian/qwen3.5-plus": {},
                        "bailian/glm-5": {},
                        "bailian/glm-4.7": {},
                    },
                    "workspace": "/home/node/.openclaw/workspace",
                    "compaction": {"mode": "safeguard"},
                    "maxConcurrent": 4,
                }
            },
            "gateway": {
                "port": 18789,
                "mode": "local",
                "bind": "lan",
                "controlUi": {
                    "allowedOrigins": [
                        f"http://127.0.0.1:{port}",
                        f"http://localhost:{port}",
                    ],
                },
                "auth": {
                    "mode": "token",
                    "token": gateway_token,
                    "password": password,
                },
            },
            "channels": {},
            "session": {"dmScope": "per-channel-peer"},
            "commands": {"native": "auto", "nativeSkills": "auto", "restart": True},
        }
        # 不写入 meta.lastTouchedAt 的 null，让 JSON 更干净
        def _drop_none(obj):
            if isinstance(obj, dict):
                return {k: _drop_none(v) for k, v in obj.items() if v is not None}
            if isinstance(obj, list):
                return [_drop_none(x) for x in obj]
            return obj
        config_path.write_text(
            json.dumps(_drop_none(default_config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        # 生成 docker-compose.yml
        await self._regenerate_compose()

        # 保存到数据库
        instance = Instance(
            id=instance_id,
            name=name,
            port=port,
            status="created"
        )
        self.db.add(instance)
        self.db.commit()
        self.db.refresh(instance)

        return instance, gateway_token

    async def delete_instance(self, instance_id: str, keep_data: bool = False) -> None:
        """删除实例：若正在运行则先停止并删除容器，再删除实例数据"""
        instance = self.db.query(Instance).filter(Instance.id == instance_id).first()
        if not instance:
            raise ValueError(f"实例 {instance_id} 不存在")

        # 若实例正在运行或容器仍存在，先停止并删除容器再删实例
        await self._stop_container(instance_id)

        # 删除目录（如果不保留数据）
        if not keep_data:
            base_path = PROJECT_ROOT / "instances" / instance_id
            if base_path.exists():
                import shutil
                shutil.rmtree(base_path)

        # 重新生成 docker-compose.yml
        await self._regenerate_compose()

        # 从数据库删除
        self.db.delete(instance)
        self.db.commit()

    async def _stop_container(self, instance_id: str) -> None:
        """停止容器"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "stop", f"openclaw-{instance_id}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

        # 删除容器
        proc = await asyncio.create_subprocess_exec(
            "docker", "rm", f"openclaw-{instance_id}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

    async def _regenerate_compose(self) -> None:
        """重新生成 docker-compose.yml"""
        instances = self.db.query(Instance).all()

        # 读取模板
        template_path = PROJECT_ROOT / "docker-compose.template.yml"
        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
        else:
            # 默认模板（Compose V2 已废弃 version，不再写入）
            template = """services:
{services}
"""

        # 生成服务配置（对齐官方 docker-compose：Gateway 18789 + Bridge 18790，卷 /home/node/.openclaw）
        # 见 openclaw 仓库 docker-compose.yml 与 docker-setup.sh
        services = []
        for inst in instances:
            # 服务名必须为字符串，否则 ID 为纯数字（如 1）时 YAML 会解析成数字键，docker compose 报 non-string key
            sid = inst.id
            service_def = f'''  "{sid}":
    image: openclaw:local
    container_name: openclaw-{sid}
    ports:
      - "{inst.port}:18789"
      - "{inst.port + 1}:18790"
    volumes:
      - ./instances/{sid}/data:/home/node/.openclaw
      - ./instances/{sid}/data/workspace:/home/node/.openclaw/workspace
    environment:
      - HOME=/home/node
      - TERM=xterm-256color
      - NODE_ENV=production
      - TZ=Asia/Shanghai
    init: true
    restart: unless-stopped
    command:
      - node
      - dist/index.js
      - gateway
      - --bind
      - lan
      - --port
      - "18789"
    networks:
      - openclaw-net'''
            services.append(service_def)

        # 写入 docker-compose.yml（含 networks）；services 不能为空否则 YAML 解析报 "services must be a mapping"
        services_block = "\n".join(services) if services else "  {}"
        compose_body = template.format(services=services_block)
        compose_content = compose_body + """
networks:
  openclaw-net:
    driver: bridge
"""
        compose_path = PROJECT_ROOT / "docker-compose.yml"
        compose_path.write_text(compose_content, encoding="utf-8")
