"""
备份管理服务
"""

import asyncio
import zipfile
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import Backup, Instance


class BackupService:
    """备份管理服务"""

    BACKUP_DIR = Path("../backup")

    def __init__(self, db: Session):
        self.db = db
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    async def create_backup(self) -> Backup:
        """创建备份"""
        # 获取所有实例
        instances = self.db.query(Instance).all()

        # 停止所有实例
        for inst in instances:
            if inst.status == "running":
                await self._stop_container(inst.id)

        # 生成备份文件名
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"openclaw-backup-{timestamp}.zip"
        backup_path = self.BACKUP_DIR / filename

        # 打包备份
        instance_count = len(instances)
        total_size = 0

        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # 备份 instances 目录
            instances_dir = Path("../instances")
            if instances_dir.exists():
                for file_path in instances_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = f"instances/{file_path.relative_to(instances_dir)}"
                        zf.write(file_path, arcname)
                        total_size += file_path.stat().st_size

            # 备份数据库
            db_path = Path("../backend/data/openclaw.db")
            if db_path.exists():
                zf.write(db_path, "database/openclaw.db")
                total_size += db_path.stat().st_size

        # 重启所有实例
        for inst in instances:
            if inst.status == "running":
                await self._start_container(inst.id)

        # 保存备份记录
        backup = Backup(
            filename=filename,
            size=total_size,
            instance_count=instance_count
        )
        self.db.add(backup)
        self.db.commit()
        self.db.refresh(backup)

        return backup

    async def delete_backup(self, backup_id: int) -> None:
        """删除备份"""
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            raise ValueError(f"备份 {backup_id} 不存在")

        # 删除文件
        backup_path = self.BACKUP_DIR / backup.filename
        if backup_path.exists():
            backup_path.unlink()

        # 删除记录
        self.db.delete(backup)
        self.db.commit()

    async def restore_backup(self, backup_id: int) -> None:
        """恢复备份"""
        backup = self.db.query(Backup).filter(Backup.id == backup_id).first()
        if not backup:
            raise ValueError(f"备份 {backup_id} 不存在")

        backup_path = self.BACKUP_DIR / backup.filename
        if not backup_path.exists():
            raise ValueError(f"备份文件不存在: {backup.filename}")

        # 停止所有实例
        instances = self.db.query(Instance).all()
        for inst in instances:
            if inst.status == "running":
                await self._stop_container(inst.id)

        # 解压备份
        with zipfile.ZipFile(backup_path, "r") as zf:
            zf.extractall("../")

        # 重启所有实例
        for inst in instances:
            await self._start_container(inst.id)

    async def _stop_container(self, instance_id: str) -> None:
        """停止容器"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "stop", f"openclaw-{instance_id}",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()

    async def _start_container(self, instance_id: str) -> None:
        """启动容器"""
        proc = await asyncio.create_subprocess_exec(
            "docker", "compose", "-f", "../docker-compose.yml", "start", instance_id,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        await proc.wait()
