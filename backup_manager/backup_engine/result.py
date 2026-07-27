"""
WorkOps Backup Execution Result — 备份执行结果
Sprint070: Real Backup Execution Engine

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidBackupExecutionError


@dataclass(frozen=True, slots=True)
class BackupExecutionResult:
    """
    备份执行结果。不可变。
    """

    backup_id: str
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidBackupExecutionError("backup_id must be a non-empty string")
        if not isinstance(self.success, bool):
            raise InvalidBackupExecutionError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidBackupExecutionError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
