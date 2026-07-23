"""
WorkOps Restore Workflow Model — 恢复工作流模型
Sprint042: Restore Workflow Foundation v1

RestoreType, RestoreStatus, RestoreWorkflow
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidRestoreRequestError


class RestoreType(Enum):
    """恢复类型。"""

    FULL = "full"
    SELECTIVE = "selective"


class RestoreStatus:
    """恢复状态常量。"""

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
            raise InvalidRestoreRequestError(f"Invalid restore status: {value}")
        return value


@dataclass(frozen=True, slots=True)
class RestoreWorkflow:
    """
    恢复工作流协调模型。不可变。

    连接 Restore → Operation → Job。
    """

    restore_id: str
    operation_id: str
    job_id: str
    backup_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidRestoreRequestError("restore_id must be a non-empty string")
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidRestoreRequestError("operation_id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidRestoreRequestError("job_id must be a non-empty string")
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidRestoreRequestError("backup_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
