"""
WorkOps Production Readiness — 生产就绪
Sprint074: WorkOps v1.0 Stable Release

ProductionReadinessStatus, ProductionReadinessReport
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidReleaseMetadataError


class ProductionReadinessStatus(Enum):
    """生产就绪状态。"""

    READY = "ready"
    NOT_READY = "not_ready"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class ProductionReadinessReport:
    """
    生产就绪报告。不可变。
    """

    status: ProductionReadinessStatus
    checks_passed: int
    checks_failed: int
    generated_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.status, ProductionReadinessStatus):
            raise InvalidReleaseMetadataError("status must be a ProductionReadinessStatus instance")
        if not isinstance(self.checks_passed, int) or self.checks_passed < 0:
            raise InvalidReleaseMetadataError("checks_passed must be a non-negative integer")
        if not isinstance(self.checks_failed, int) or self.checks_failed < 0:
            raise InvalidReleaseMetadataError("checks_failed must be a non-negative integer")
        if self.generated_at is None:
            object.__setattr__(self, "generated_at", datetime.now(timezone.utc))
