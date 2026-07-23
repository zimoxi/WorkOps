"""
WorkOps Health History — 健康历史模型
Sprint043: Device Health Monitoring Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .status import HealthStatus
from .errors import InvalidHealthRequestError


@dataclass(frozen=True, slots=True)
class HealthHistory:
    """
    健康历史记录。不可变。
    """

    check_id: str
    device_id: str
    status: HealthStatus
    checked_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.check_id, str) or not self.check_id.strip():
            raise InvalidHealthRequestError("check_id must be a non-empty string")
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidHealthRequestError("device_id must be a non-empty string")
        if not isinstance(self.status, HealthStatus):
            raise InvalidHealthRequestError("status must be a HealthStatus instance")
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", datetime.now(timezone.utc))
