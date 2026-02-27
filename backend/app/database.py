"""
数据库连接和会话管理
"""

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base

# 项目根目录（backend 的上一级），用于 docker-compose、instances 等路径
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 数据库文件路径
DB_PATH = Path(__file__).parent.parent / "data" / "openclaw.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

# 创建引擎
engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    connect_args={"check_same_thread": False},
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """初始化数据库，创建所有表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """获取数据库会话（用于依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
