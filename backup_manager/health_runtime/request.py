"""
WorkOps Health Execution Request — 健康执行请求
Sprint055: Health Runtime Integration Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidHealthExecutionRequestError


@dataclass(frozen=True, slots=True)
class HealthExecutionRequest:
    """
    健康执行请求。不可变。
    """

    health_id: str
    operation_id: str
    execution_id: str
    adapter_id: str
    device_id: str
    created_at: datetime = None

    def __post_init__(self):
        for field_name in ["health_id", "operation_id", "execution_id", "adapter_id", "device_id"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidHealthExecutionRequestError(f"{field_name} must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
