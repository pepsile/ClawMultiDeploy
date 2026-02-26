"""
FastAPI 主入口
提供 OpenClaw 多实例管理 API
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers import instances, backups, system


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    init_db()
    yield
    # 关闭时清理资源


app = FastAPI(
    title="ClawMultiDeploy API",
    description="OpenClaw 多实例管理系统",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(instances.router, prefix="/api", tags=["instances"])
app.include_router(backups.router, prefix="/api", tags=["backups"])
app.include_router(system.router, prefix="/api", tags=["system"])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "ClawMultiDeploy API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}
