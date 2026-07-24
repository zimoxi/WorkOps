"""
WorkOps PVE API Request — PVE API 请求
Sprint059: PVE API Runtime Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidPVERuntimeSessionError


@dataclass(frozen=True, slots=True)
class PVEAPIRequest:
    """
    PVE API 请求。不可变。

    只允许预定义的只读操作标识符。
    """

    session_id: str
    operation: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidPVERuntimeSessionError("session_id must be a non-empty string")
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise InvalidPVERuntimeSessionError("operation must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_pve_request(request: PVEAPIRequest) -> None:
    """
    验证 PVE API 请求。

    Args:
        request: PVE API 请求

    Raises:
        InvalidPVERuntimeSessionError: 验证失败
    """
    if not isinstance(request, PVEAPIRequest):
        raise InvalidPVERuntimeSessionError("request must be a PVEAPIRequest instance")
