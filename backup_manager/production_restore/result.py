"""
WorkOps Production Restore Result — 生产恢复结果
Sprint062: Production Restore Execution Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import ProductionRestoreStatus
from .errors import InvalidProductionRestoreRequestError


@dataclass(frozen=True, slots=True)
class ProductionRestoreResult:
    """
    生产恢复结果。不可变。
    """

    restore_id: str
    status: ProductionRestoreStatus
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise InvalidProductionRestoreRequestError("restore_id must be a non-empty string")
        if not isinstance(self.status, ProductionRestoreStatus):
            raise InvalidProductionRestoreRequestError("status must be a ProductionRestoreStatus instance")
        if not isinstance(self.success, bool):
            raise InvalidProductionRestoreRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidProductionRestoreRequestError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
