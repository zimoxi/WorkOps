"""
WorkOps Backup Policy — 备份策略
Sprint029: Backup Workflow Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .errors import InvalidPolicyError


@dataclass(frozen=True, slots=True)
class BackupPolicy:
    """
    备份策略。不可变。
    """

    policy_id: str
    daily_retention: int = 7
    weekly_retention: int = 4
    monthly_retention: int = 12

    def __post_init__(self):
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise InvalidPolicyError("policy_id must be a non-empty string")
        if not isinstance(self.daily_retention, int) or isinstance(self.daily_retention, bool):
            raise InvalidPolicyError("daily_retention must be an integer")
        if self.daily_retention < 0:
            raise InvalidPolicyError("daily_retention must be >= 0")
        if not isinstance(self.weekly_retention, int) or isinstance(self.weekly_retention, bool):
            raise InvalidPolicyError("weekly_retention must be an integer")
        if self.weekly_retention < 0:
            raise InvalidPolicyError("weekly_retention must be >= 0")
        if not isinstance(self.monthly_retention, int) or isinstance(self.monthly_retention, bool):
            raise InvalidPolicyError("monthly_retention must be an integer")
        if self.monthly_retention < 0:
            raise InvalidPolicyError("monthly_retention must be >= 0")
