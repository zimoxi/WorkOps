"""
WorkOps Backup Workflow Model — 备份工作流模型
Sprint041: Backup Workflow Foundation v1

BackupType, BackupStatus, BackupWorkflow
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .workflow_errors import InvalidBackupRequestError


class BackupType(Enum):
    """备份类型。"""

    FULL = "full"
    INCREMENTAL = "incremental"


class BackupStatus:
    """备份状态常量。"""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

    _VALID = {"created", "queued", "running", "success", "failed", "cancelled"}

    @classmethod
    def validate(cls, value: str) -> str:
        if value not in cls._VALID:
            raise InvalidBackupRequestError(f"Invalid backup status: {value}")
        return value


@dataclass(frozen=True, slots=True)
class BackupWorkflow:
    """
    备份工作流协调模型。不可变。

    连接 Backup → Operation → Job。
    """

    backup_id: str
    operation_id: str
    job_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidBackupRequestError("backup_id must be a non-empty string")
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidBackupRequestError("operation_id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidBackupRequestError("job_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
