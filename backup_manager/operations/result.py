"""
WorkOps Operation Result — 操作结果模型
Sprint038: Operation Orchestration Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .operation import OperationStatus
from .errors import InvalidOperationError


@dataclass(frozen=True, slots=True)
class OperationResult:
    """
    操作结果。不可变。
    """

    operation_id: str
    status: OperationStatus
    success: bool
    message: str
    finished_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidOperationError("operation_id must be a non-empty string")
        if not isinstance(self.status, OperationStatus):
            raise InvalidOperationError("status must be an OperationStatus instance")
        if not isinstance(self.success, bool):
            raise InvalidOperationError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidOperationError("message must be a string")
        if self.finished_at is None:
            object.__setattr__(self, "finished_at", datetime.now(timezone.utc))
