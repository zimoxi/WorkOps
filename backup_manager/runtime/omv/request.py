"""
WorkOps OMV API Request — OMV API 请求
Sprint060: OMV API Runtime Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidOMVRuntimeSessionError


@dataclass(frozen=True, slots=True)
class OMVAPIRequest:
    """
    OMV API 请求。不可变。

    只允许预定义的只读操作标识符。
    """

    session_id: str
    operation: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidOMVRuntimeSessionError("session_id must be a non-empty string")
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise InvalidOMVRuntimeSessionError("operation must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_omv_request(request: OMVAPIRequest) -> None:
    """
    验证 OMV API 请求。

    Args:
        request: OMV API 请求

    Raises:
        InvalidOMVRuntimeSessionError: 验证失败
    """
    if not isinstance(request, OMVAPIRequest):
        raise InvalidOMVRuntimeSessionError("request must be an OMVAPIRequest instance")
