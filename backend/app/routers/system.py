"""
系统状态路由
"""

import subprocess

from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models import Instance
from app.schemas import ApiResponse, SystemStatus

router = APIRouter()


def check_docker() -> bool:
    """检查 Docker 是否运行"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except Exception:
        return False


@router.get("/system/status", response_model=ApiResponse)
async def get_system_status():
    """获取系统状态"""
    db = SessionLocal()
    try:
        instances = db.query(Instance).all()
        running_count = sum(1 for i in instances if i.status == "running")

        status = SystemStatus(
            docker_running=check_docker(),
            base_port=18789,
            instance_count=len(instances),
            running_count=running_count
        )
        return ApiResponse(data={"status": status.model_dump()})
    finally:
        db.close()


@router.get("/system/ports", response_model=ApiResponse)
async def get_available_ports():
    """获取可用端口范围"""
    db = SessionLocal()
    try:
        used_ports = [i.port for i in db.query(Instance.port).all()]
        # 推荐端口：从 18789 开始，跳过已使用的
        base_port = 18789
        recommended = []
        port = base_port
        while len(recommended) < 10:  # 推荐 10 个可用端口
            if port not in used_ports:
                recommended.append(port)
            port += 1

        return ApiResponse(data={
            "used_ports": used_ports,
            "recommended_ports": recommended,
            "base_port": base_port
        })
    finally:
        db.close()
