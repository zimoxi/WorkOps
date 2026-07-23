"""
WorkOps Policy Model — 策略模型
Sprint044: Policy Engine Foundation

PolicyRule, Policy — frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .rule import PolicyEffect, PolicyType
from .errors import InvalidPolicyError


@dataclass(frozen=True, slots=True)
class PolicyRule:
    """
    策略规则。不可变。
    """

    rule_id: str
    policy_type: PolicyType
    effect: PolicyEffect
    description: str

    def __post_init__(self):
        if not isinstance(self.rule_id, str) or not self.rule_id.strip():
            raise InvalidPolicyError("rule_id must be a non-empty string")
        if not isinstance(self.policy_type, PolicyType):
            raise InvalidPolicyError("policy_type must be a PolicyType instance")
        if not isinstance(self.effect, PolicyEffect):
            raise InvalidPolicyError("effect must be a PolicyEffect instance")
        if not isinstance(self.description, str) or not self.description.strip():
            raise InvalidPolicyError("description must be a non-empty string")


@dataclass(frozen=True, slots=True)
class Policy:
    """
    策略。不可变。rules 为 tuple。
    """

    policy_id: str
    name: str
    rules: tuple  # tuple[PolicyRule, ...]
    enabled: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise InvalidPolicyError("policy_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidPolicyError("name must be a non-empty string")
        if not isinstance(self.rules, tuple):
            raise InvalidPolicyError("rules must be a tuple")
        for rule in self.rules:
            if not isinstance(rule, PolicyRule):
                raise InvalidPolicyError("All rules must be PolicyRule instances")
        if not isinstance(self.enabled, bool):
            raise InvalidPolicyError("enabled must be a bool")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
