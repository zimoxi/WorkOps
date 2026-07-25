"""
WorkOps Release Validator — 发布验证器
Sprint065: Release Candidate Foundation

ReleaseCheckResult, ReleaseValidator
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from .capability import CapabilityReport
from .errors import InvalidReleaseMetadataError


@dataclass(frozen=True, slots=True)
class ReleaseCheckResult:
    """
    发布检查结果。不可变。
    """

    success: bool
    message: str
    checked_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.success, bool):
            raise InvalidReleaseMetadataError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidReleaseMetadataError("message must be a string")
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", datetime.now(timezone.utc))


class ReleaseValidator(ABC):
    """
    发布验证器接口。

    只定义接口。不实现 CI/CD。
    """

    @abstractmethod
    def validate(self, report: CapabilityReport) -> bool:
        """
        验证发布。

        Args:
            report: 能力报告

        Returns:
            bool
        """
        ...
