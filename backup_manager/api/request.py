"""
WorkOps Operation Request Model — 操作请求模型
Sprint045: Unified Operation API Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from ..operations.operation import OperationType
from .errors import InvalidOperationRequestError


@dataclass(frozen=True, slots=True)
class OperationRequestModel:
    """
    操作请求模型。不可变。
    """

    request_id: str
    operation_type: OperationType
    device_id: str | None = None
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidOperationRequestError("request_id must be a non-empty string")
        if not isinstance(self.operation_type, OperationType):
            raise InvalidOperationRequestError("operation_type must be an OperationType instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
