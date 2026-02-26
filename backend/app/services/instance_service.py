"""
实例业务逻辑服务
"""

import asyncio
import json
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Instance


class InstanceService:
    """实例管理服务"""

    BASE_PORT = 18789

    def __init__(self, db: Session):
        self.db = db

    def _get_next_port(self) -> int:
        """获取下一个可用端口"""
        used_ports = {i.port for i in self.db.query(Instance.port).all()}
        port = self.BASE_PORT
        while port in used_ports:
            port += 1
        return port

    async def create_instance(self, instance_id: str, name: str) -> Instance:
        """创建新实例"""
        # 分配端口
        port = self._get_next_port()

        # 创建目录结构
        base_path = Path(f"../instances/{instance_id}")
        (base_path / "data").mkdir(parents=True, exist_ok=True)
        (base_path / "logs").mkdir(parents=True, exist_ok=True)

        # 创建默认配置文件
        config_path = base_path / "data" / "openclaw.json"
        default_config = {
            "gateway": {
                "mode": "local",
                "token": "",
                "port": 18789
            },
            "agents": {
                "defaults": {
                    "model": "gpt-4",
                    "sandbox": {
                        "mode": "non-main",
                        "scope": "agent"
                    }
                }
            },
            "channels": [],
            "tools": {
                "defaults": ["*"]
            }
        }
        config_path.write_text(
            json.dumps(default_config, indent=4, ensure_ascii=False),
            encoding="utf-8"
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

        return instance

    async def delete_instance(self, instance_id: str, keep_data: bool = False) -> None:
        """删除实例"""
        instance = self.db.query(Instance).filter(Instance.id == instance_id).first()
        if not instance:
            raise ValueError(f"实例 {instance_id} 不存在")

        # 停止容器
        await self._stop_container(instance_id)

        # 删除目录（如果不保留数据）
        if not keep_data:
            base_path = Path(f"../instances/{instance_id}")
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
        template_path = Path("../docker-compose.template.yml")
        if template_path.exists():
            template = template_path.read_text(encoding="utf-8")
        else:
            # 默认模板
            template = """version: "3.8"
services:
{services}
"""

        # 生成服务配置
        services = []
        for inst in instances:
            service_def = f'''  {inst.id}:
    image: openclaw:local
    container_name: openclaw-{inst.id}
    ports:
      - "{inst.port}:18789"
    volumes:
      - ./instances/{inst.id}/data:/root/.openclaw
      - ./instances/{inst.id}/logs:/var/log/openclaw
    environment:
      - TZ=Asia/Shanghai
      - LANG=C.UTF-8
    restart: unless-stopped'''
            services.append(service_def)

        # 写入 docker-compose.yml
        compose_content = template.format(services="\n".join(services))
        compose_path = Path("../docker-compose.yml")
        compose_path.write_text(compose_content, encoding="utf-8")
