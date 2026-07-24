"""
WorkOps Health Execution Result — 健康执行结果
Sprint055: Health Runtime Integration Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import HealthExecutionStatus
from .errors import InvalidHealthExecutionRequestError


@dataclass(frozen=True, slots=True)
class HealthExecutionResult:
    """
    健康执行结果。不可变。
    """

    health_id: str
    status: HealthExecutionStatus
    healthy: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.health_id, str) or not self.health_id.strip():
            raise InvalidHealthExecutionRequestError("health_id must be a non-empty string")
        if not isinstance(self.status, HealthExecutionStatus):
            raise InvalidHealthExecutionRequestError("status must be a HealthExecutionStatus instance")
        if not isinstance(self.healthy, bool):
            raise InvalidHealthExecutionRequestError("healthy must be a bool")
        if not isinstance(self.message, str):
            raise InvalidHealthExecutionRequestError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
