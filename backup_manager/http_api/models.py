"""
WorkOps HTTP API Models — HTTP API 模型
Sprint066: HTTP API Runtime Foundation

HTTPRequest, HTTPResponse
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidHTTPRequestError


@dataclass(frozen=True, slots=True)
class HTTPRequest:
    """
    HTTP 请求。不可变。
    """

    request_id: str
    endpoint: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidHTTPRequestError("request_id must be a non-empty string")
        if not isinstance(self.endpoint, str) or not self.endpoint.strip():
            raise InvalidHTTPRequestError("endpoint must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class HTTPResponse:
    """
    HTTP 响应。不可变。
    """

    request_id: str
    status_code: int
    message: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidHTTPRequestError("request_id must be a non-empty string")
        if not isinstance(self.status_code, int) or self.status_code < 100 or self.status_code > 599:
            raise InvalidHTTPRequestError("status_code must be a valid HTTP status code (100-599)")
        if not isinstance(self.message, str):
            raise InvalidHTTPRequestError("message must be a string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
