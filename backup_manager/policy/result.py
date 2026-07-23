"""
WorkOps Policy Evaluation Result — 策略评估结果
Sprint044: Policy Engine Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .rule import PolicyEffect
from .errors import InvalidPolicyError


@dataclass(frozen=True, slots=True)
class PolicyEvaluationResult:
    """
    策略评估结果。不可变。
    """

    request_id: str
    allowed: bool
    effect: PolicyEffect
    message: str
    evaluated_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.request_id, str) or not self.request_id.strip():
            raise InvalidPolicyError("request_id must be a non-empty string")
        if not isinstance(self.allowed, bool):
            raise InvalidPolicyError("allowed must be a bool")
        if not isinstance(self.effect, PolicyEffect):
            raise InvalidPolicyError("effect must be a PolicyEffect instance")
        if not isinstance(self.message, str):
            raise InvalidPolicyError("message must be a string")
        if self.evaluated_at is None:
            object.__setattr__(self, "evaluated_at", datetime.now(timezone.utc))
