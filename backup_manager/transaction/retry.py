"""
WorkOps Retry Policy — 重试策略
Sprint056: Operation Transaction System Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .errors import InvalidTransactionError


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """
    重试策略。不可变。
    """

    max_attempts: int
    retry_enabled: bool = True

    def __post_init__(self):
        if not isinstance(self.max_attempts, int) or self.max_attempts < 0:
            raise InvalidTransactionError("max_attempts must be a non-negative integer")
        if not isinstance(self.retry_enabled, bool):
            raise InvalidTransactionError("retry_enabled must be a bool")
