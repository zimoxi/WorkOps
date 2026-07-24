"""
WorkOps Restore Execution Result — 恢复执行结果
Sprint054: Restore Execution Pipeline Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import RestoreExecutionStatus
from .errors import InvalidRestoreExecutionRequestError


@dataclass(frozen=True, slots=True)
class RestoreExecutionResult:
    """
    恢复执行结果。不可变。
    """

    restore_id: str
    status: RestoreExecutionStatus
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidRestoreExecutionRequestError("restore_id must be a non-empty string")
        if not isinstance(self.status, RestoreExecutionStatus):
            raise InvalidRestoreExecutionRequestError("status must be a RestoreExecutionStatus instance")
        if not isinstance(self.success, bool):
            raise InvalidRestoreExecutionRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidRestoreExecutionRequestError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
