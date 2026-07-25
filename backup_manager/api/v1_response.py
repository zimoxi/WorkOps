"""
WorkOps API Response — API 响应模型
Sprint064: API Service Layer Foundation

APIResponseStatus, APIResponse
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .v1_errors import InvalidAPIRequestError


class APIResponseStatus(Enum):
    """API 响应状态。"""

    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class APIResponse:
    """
    API 响应。不可变。
    """

    request_id: str
    status: APIResponseStatus
    message: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidAPIRequestError("request_id must be a non-empty string")
        if not isinstance(self.status, APIResponseStatus):
            raise InvalidAPIRequestError("status must be an APIResponseStatus instance")
        if not isinstance(self.message, str):
            raise InvalidAPIRequestError("message must be a string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
