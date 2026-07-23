"""
WorkOps Restore Request — 恢复请求模型
Sprint042: Restore Workflow Foundation v1

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import RestoreType
from .errors import InvalidRestoreRequestError


@dataclass(frozen=True, slots=True)
class RestoreRequest:
    """
    恢复请求。不可变。
    """

    restore_id: str
    device_id: str
    backup_id: str
    restore_type: RestoreType
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidRestoreRequestError("restore_id must be a non-empty string")
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidRestoreRequestError("device_id must be a non-empty string")
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidRestoreRequestError("backup_id must be a non-empty string")
        if not isinstance(self.restore_type, RestoreType):
            raise InvalidRestoreRequestError("restore_type must be a RestoreType instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
