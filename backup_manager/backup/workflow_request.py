"""
WorkOps Backup Request — 备份请求模型
Sprint041: Backup Workflow Foundation v1

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .workflow_model import BackupType
from .workflow_errors import InvalidBackupRequestError


@dataclass(frozen=True, slots=True)
class BackupRequest:
    """
    备份请求。不可变。
    """

    backup_id: str
    device_id: str
    backup_type: BackupType
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidBackupRequestError("backup_id must be a non-empty string")
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidBackupRequestError("device_id must be a non-empty string")
        if not isinstance(self.backup_type, BackupType):
            raise InvalidBackupRequestError("backup_type must be a BackupType instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
