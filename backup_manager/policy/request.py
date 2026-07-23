"""
WorkOps Policy Evaluation Request — 策略评估请求
Sprint044: Policy Engine Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidPolicyError


@dataclass(frozen=True, slots=True)
class PolicyEvaluationRequest:
    """
    策略评估请求。不可变。
    """

    request_id: str
    operation_type: str
    device_id: str | None = None
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidPolicyError("request_id must be a non-empty string")
        if not isinstance(self.operation_type, str) or not self.operation_type.strip():
            raise InvalidPolicyError("operation_type must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
