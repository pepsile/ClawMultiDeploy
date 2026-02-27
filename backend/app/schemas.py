"""
Pydantic 模型（请求/响应数据验证）
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class InstanceCreate(BaseModel):
    """创建实例请求"""
    id: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    name: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200, description="Gateway 控制台登录密码")


class InstanceResponse(BaseModel):
    """实例响应"""
    id: str
    name: str
    port: int
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True


class InstanceConfig(BaseModel):
    """实例配置（openclaw.json）"""
    content: str = Field(..., description="JSON5 格式的配置内容")


class BackupResponse(BaseModel):
    """备份响应"""
    id: int
    filename: str
    size: int
    instance_count: int
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class SystemStatus(BaseModel):
    """系统状态"""
    docker_running: bool
    base_port: int
    instance_count: int
    running_count: int


class DeviceApproveRequest(BaseModel):
    """设备配对批准请求"""
    requestId: str = Field(..., min_length=1, description="待批准的设备请求 ID")


class ApiResponse(BaseModel):
    """统一 API 响应格式"""
    code: int = 0
    data: Optional[dict] = None
    message: str = "success"
