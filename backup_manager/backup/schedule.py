"""
WorkOps Backup Schedule — 备份调度
Sprint029: Backup Workflow Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .errors import InvalidBackupJobError


@dataclass(frozen=True, slots=True)
class BackupSchedule:
    """
    备份调度。不可变。
    """

    schedule_id: str
    cron_expression: str
    enabled: bool = True

    def __post_init__(self):
        if not isinstance(self.schedule_id, str) or not self.schedule_id.strip():
            raise InvalidBackupJobError("schedule_id must be a non-empty string")
        if not isinstance(self.cron_expression, str) or not self.cron_expression.strip():
            raise InvalidBackupJobError("cron_expression must be a non-empty string")
        if not isinstance(self.enabled, bool):
            raise InvalidBackupJobError("enabled must be a bool")
