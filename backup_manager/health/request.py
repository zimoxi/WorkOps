"""
WorkOps Health Check Request — 健康检查请求模型
Sprint043: Device Health Monitoring Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .status import HealthCheckType
from .errors import InvalidHealthRequestError


@dataclass(frozen=True, slots=True)
class HealthCheckRequest:
    """
    健康检查请求。不可变。
    """

    check_id: str
    device_id: str
    check_type: HealthCheckType
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.check_id, str) or not self.check_id.strip():
            raise InvalidHealthRequestError("check_id must be a non-empty string")
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidHealthRequestError("device_id must be a non-empty string")
        if not isinstance(self.check_type, HealthCheckType):
            raise InvalidHealthRequestError("check_type must be a HealthCheckType instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
