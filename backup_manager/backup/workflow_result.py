"""
WorkOps Backup Workflow Result — 备份工作流结果
Sprint041: Backup Workflow Foundation v1

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .workflow_model import BackupStatus
from .workflow_errors import InvalidBackupRequestError


@dataclass(frozen=True, slots=True)
class BackupResult:
    """
    备份结果。不可变。
    """

    backup_id: str
    status: str
    success: bool
    message: str
    finished_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidBackupRequestError("backup_id must be a non-empty string")
        BackupStatus.validate(self.status)
        if not isinstance(self.success, bool):
            raise InvalidBackupRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidBackupRequestError("message must be a string")
        if self.finished_at is None:
            object.__setattr__(self, "finished_at", datetime.now(timezone.utc))
