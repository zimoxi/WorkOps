"""
WorkOps API Request — API 请求模型
Sprint064: API Service Layer Foundation

APIRequestType, APIRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .v1_errors import InvalidAPIRequestError


class APIRequestType(Enum):
    """API 请求类型。"""

    BACKUP = "backup"
    RESTORE = "restore"
    HEALTH = "health"
    STATUS = "status"


@dataclass(frozen=True, slots=True)
class APIRequest:
    """
    API 请求。不可变。
    """

    request_id: str
    request_type: APIRequestType
    resource_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidAPIRequestError("request_id must be a non-empty string")
        if not isinstance(self.request_type, APIRequestType):
            raise InvalidAPIRequestError("request_type must be an APIRequestType instance")
        if not isinstance(self.resource_id, str) or not self.resource_id.strip():
            raise InvalidAPIRequestError("resource_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_api_request(request: APIRequest) -> None:
    """
    验证 API 请求。

    Args:
        request: API 请求

    Raises:
        InvalidAPIRequestError: 验证失败
    """
    if not isinstance(request, APIRequest):
        raise InvalidAPIRequestError("request must be an APIRequest instance")
