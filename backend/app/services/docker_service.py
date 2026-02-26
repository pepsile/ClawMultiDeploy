"""
Docker 操作服务
"""

import asyncio
from pathlib import Path
from typing import AsyncGenerator


class DockerService:
    """Docker 操作服务"""

    async def start_instance(self, instance_id: str) -> None:
        """启动实例容器"""
        # 先确保容器存在（通过 compose 创建）
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", "-f", "../docker-compose.yml", "up", "-d", instance_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"启动失败: {stderr.decode()}")

    async def stop_instance(self, instance_id: str) -> None:
        """停止实例容器"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", "-f", "../docker-compose.yml", "stop", instance_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"停止失败: {stderr.decode()}")

    async def init_instance(self, instance_id: str) -> str:
        """初始化实例（运行 onboard）"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", "-f", "../docker-compose.yml", "exec", "-T",
            instance_id, "openclaw", "onboard",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        output = stdout.decode() + stderr.decode()
        return output

    async def stream_logs(self, instance_id: str) -> AsyncGenerator[str, None]:
        """实时流式日志"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "logs", "-f", f"openclaw-{instance_id}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT
        )

        if proc.stdout:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                yield line.decode().rstrip()

    async def get_container_status(self, instance_id: str) -> str:
        """获取容器状态"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "ps", "-a", "--filter", f"name=openclaw-{instance_id}",
            "--format", "{{.State}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        status = stdout.decode().strip()
        return status if status else "not_created"
