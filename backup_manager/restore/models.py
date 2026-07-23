"""
WorkOps Restore Job Model — 恢复任务模型
Sprint036: Restore Workflow Foundation

frozen dataclass。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .state import RestoreExecutionState
from .errors import InvalidRestoreJobError


@dataclass(frozen=True, slots=True)
class RestoreJob:
    """
    恢复任务。不可变。
    """

    restore_id: str
    source_backup_id: str
    target_device_id: str
    status: RestoreExecutionState = RestoreExecutionState.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidRestoreJobError("restore_id must be a non-empty string")
        if not isinstance(self.source_backup_id, str) or not self.source_backup_id.strip():
            raise InvalidRestoreJobError("source_backup_id must be a non-empty string")
        if not isinstance(self.target_device_id, str) or not self.target_device_id.strip():
            raise InvalidRestoreJobError("target_device_id must be a non-empty string")
        if not isinstance(self.status, RestoreExecutionState):
            raise InvalidRestoreJobError("status must be a RestoreExecutionState instance")
