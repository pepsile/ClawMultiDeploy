"""
Docker 操作服务
"""

import asyncio
import logging
from pathlib import Path
from typing import AsyncGenerator

from app.database import PROJECT_ROOT

logger = logging.getLogger(__name__)


def _decode(b: bytes) -> str:
    return b.decode("utf-8", errors="replace").strip()


class DockerService:
    """Docker 操作服务"""

    def _compose_file(self) -> Path:
        return PROJECT_ROOT / "docker-compose.yml"

    async def start_instance(self, instance_id: str) -> None:
        """启动实例容器"""
        compose_path = self._compose_file()
        logger.info("start_instance: instance_id=%s, PROJECT_ROOT=%s, compose_path=%s", instance_id, PROJECT_ROOT, compose_path)

        if not compose_path.exists():
            logger.error("docker-compose.yml 不存在: %s", compose_path)
            raise FileNotFoundError(
                f"docker-compose.yml 不存在: {compose_path}，请先创建实例以生成该文件"
            )

        cmd = ["docker", "compose", "-f", str(compose_path), "up", "-d", instance_id]
        logger.info("执行命令: %s, cwd=%s", " ".join(cmd), PROJECT_ROOT)

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout, stderr = await proc.communicate()

        out, err = _decode(stdout), _decode(stderr)
        logger.info("docker compose 返回: returncode=%s, stdout=%r, stderr=%r", proc.returncode, out, err)

        if proc.returncode != 0:
            msg = err or out or "未知错误"
            logger.error("启动失败: %s", msg)
            hint = ""
            if "size validation" in msg or "failed precondition" in msg:
                hint = " 建议: 若为镜像拉取校验失败，请从源码构建镜像: git clone https://github.com/openclaw/openclaw.git && cd openclaw && docker build -t openclaw:local -f Dockerfile ."
            raise RuntimeError(f"启动失败: {msg}{hint}")

    async def stop_instance(self, instance_id: str) -> None:
        """停止实例容器"""
        compose_path = self._compose_file()
        if not compose_path.exists():
            return
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "compose",
            "-f",
            str(compose_path),
            "stop",
            instance_id,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(PROJECT_ROOT),
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            out, err = _decode(stdout), _decode(stderr)
            raise RuntimeError(f"停止失败: {err or out or '未知错误'}")

    async def init_instance(self, instance_id: str) -> str:
        """初始化实例（运行 onboard，对齐官方：docker compose run --rm openclaw-cli onboard）"""
        data_dir = PROJECT_ROOT / "instances" / instance_id / "data"
        if not data_dir.exists():
            raise FileNotFoundError(f"实例数据目录不存在: {data_dir}")
        # 与官方一致：挂载 .openclaw 目录，运行 node dist/index.js onboard
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "run",
            "--rm",
            "-v",
            f"{data_dir}:/home/node/.openclaw",
            "openclaw:local",
            "node",
            "dist/index.js",
            "onboard",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        return _decode(stdout) + _decode(stderr)

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
                yield _decode(line)

    async def get_container_status(self, instance_id: str) -> str:
        """获取容器状态"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "ps", "-a", "--filter", f"name=openclaw-{instance_id}",
            "--format", "{{.State}}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()

        status = _decode(stdout)
        return status if status else "not_created"

    async def devices_list(self, instance_id: str, token: str) -> str:
        """在实例容器内执行 openclaw devices list --json，需传入 gateway token"""
        cmd = [
            "docker", "exec", f"openclaw-{instance_id}",
            "node", "dist/index.js", "devices", "list", "--json",
            "--url", "ws://127.0.0.1:18789",
            "--token", token,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        out, err = _decode(stdout), _decode(stderr)
        if proc.returncode != 0:
            raise RuntimeError(f"devices list 失败: {err or out or '未知错误'}")
        return out

    async def devices_approve(self, instance_id: str, request_id: str, token: str) -> None:
        """在实例容器内执行 openclaw devices approve <requestId>"""
        cmd = [
            "docker", "exec", f"openclaw-{instance_id}",
            "node", "dist/index.js", "devices", "approve", request_id,
            "--url", "ws://127.0.0.1:18789",
            "--token", token,
        ]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        out, err = _decode(stdout), _decode(stderr)
        if proc.returncode != 0:
            raise RuntimeError(f"devices approve 失败: {err or out or '未知错误'}")
