"""
WorkOps Restore Execution Result — 恢复执行结果
Sprint071: Real Restore Execution Engine

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidRestoreExecutionError


@dataclass(frozen=True, slots=True)
class RestoreExecutionResult:
    """
    恢复执行结果。不可变。
    """

    restore_id: str
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidRestoreExecutionError("restore_id must be a non-empty string")
        if not isinstance(self.success, bool):
            raise InvalidRestoreExecutionError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidRestoreExecutionError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
