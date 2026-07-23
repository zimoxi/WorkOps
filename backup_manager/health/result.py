"""
WorkOps Health Result — 健康检查结果模型
Sprint043: Device Health Monitoring Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .status import HealthStatus
from .errors import InvalidHealthRequestError


@dataclass(frozen=True, slots=True)
class HealthResult:
    """
    健康检查结果。不可变。
    """

    check_id: str
    status: HealthStatus
    success: bool
    message: str
    checked_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.check_id, str) or not self.check_id.strip():
            raise InvalidHealthRequestError("check_id must be a non-empty string")
        if not isinstance(self.status, HealthStatus):
            raise InvalidHealthRequestError("status must be a HealthStatus instance")
        if not isinstance(self.success, bool):
            raise InvalidHealthRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidHealthRequestError("message must be a string")
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", datetime.now(timezone.utc))
