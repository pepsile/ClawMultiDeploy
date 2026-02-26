"""
备份管理路由
"""

from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Backup
from app.schemas import ApiResponse, BackupResponse
from app.services.backup_service import BackupService

router = APIRouter()


@router.get("/backups", response_model=ApiResponse)
async def get_backups(db: Session = Depends(get_db)):
    """获取备份列表"""
    backups = db.query(Backup).order_by(Backup.created_at.desc()).all()
    return ApiResponse(
        data={"backups": [b.to_dict() for b in backups]}
    )


@router.post("/backups", response_model=ApiResponse)
async def create_backup(db: Session = Depends(get_db)):
    """创建备份"""
    service = BackupService(db)
    try:
        backup = await service.create_backup()
        return ApiResponse(
            data={"backup": backup.to_dict()},
            message="备份创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/backups/{backup_id}", response_model=ApiResponse)
async def delete_backup(backup_id: int, db: Session = Depends(get_db)):
    """删除备份"""
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    service = BackupService(db)
    try:
        await service.delete_backup(backup_id)
        return ApiResponse(message="备份删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backups/{backup_id}/restore", response_model=ApiResponse)
async def restore_backup(backup_id: int, db: Session = Depends(get_db)):
    """恢复备份"""
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    service = BackupService(db)
    try:
        await service.restore_backup(backup_id)
        return ApiResponse(message="备份恢复成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
