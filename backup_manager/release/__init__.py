"""
WorkOps Release Domain — 发布域
Sprint065/Sprint074: Release Candidate Foundation / WorkOps v1.0 Stable Release
"""

from .errors import (
    ReleaseError,
    InvalidReleaseMetadataError,
    ReleaseValidationError,
    ReleaseUnavailableError,
    StableReleaseError,
    ReleaseBlockedError,
    InvalidReleaseStateError,
)
from .version import ReleaseVersion
from .metadata import BuildMetadata
from .capability import CapabilityReport
from .validator import ReleaseCheckResult, ReleaseValidator
from .stable import StableVersion
from .readiness import ProductionReadinessStatus, ProductionReadinessReport
from .checklist import ReleaseChecklistItem, ReleaseChecklist


class StableReleaseValidator:
    """
    稳定发布验证器接口。

    只定义接口。
    """

    def validate(self, report: ProductionReadinessReport) -> bool:
        """
        验证生产就绪报告。

        Args:
            report: 生产就绪报告

        Returns:
            bool
        """
        raise NotImplementedError


__all__ = [
    # Sprint065
    "ReleaseError",
    "InvalidReleaseMetadataError",
    "ReleaseValidationError",
    "ReleaseUnavailableError",
    "ReleaseVersion",
    "BuildMetadata",
    "CapabilityReport",
    "ReleaseCheckResult",
    "ReleaseValidator",
    # Sprint074
    "StableReleaseError",
    "ReleaseBlockedError",
    "InvalidReleaseStateError",
    "StableVersion",
    "ProductionReadinessStatus",
    "ProductionReadinessReport",
    "ReleaseChecklistItem",
    "ReleaseChecklist",
    "StableReleaseValidator",
]
