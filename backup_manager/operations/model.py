"""
WorkOps Operation Request Model — 操作请求模型
Sprint038: Operation Orchestration Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .operation import OperationType
from .errors import InvalidOperationError


@dataclass(frozen=True, slots=True)
class OperationRequest:
    """
    操作请求。不可变。
    """

    operation_id: str
    operation_type: OperationType
    device_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidOperationError("operation_id must be a non-empty string")
        if not isinstance(self.operation_type, OperationType):
            raise InvalidOperationError("operation_type must be an OperationType instance")
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidOperationError("device_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
