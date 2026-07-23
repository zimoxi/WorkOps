"""
WorkOps Restore Workflow Result — 恢复工作流结果
Sprint042: Restore Workflow Foundation v1

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import RestoreStatus
from .errors import InvalidRestoreRequestError


@dataclass(frozen=True, slots=True)
class RestoreResult:
    """
    恢复结果。不可变。
    """

    restore_id: str
    status: str
    success: bool
    message: str
    finished_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidRestoreRequestError("restore_id must be a non-empty string")
        RestoreStatus.validate(self.status)
        if not isinstance(self.success, bool):
            raise InvalidRestoreRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidRestoreRequestError("message must be a string")
        if self.finished_at is None:
            object.__setattr__(self, "finished_at", datetime.now(timezone.utc))
