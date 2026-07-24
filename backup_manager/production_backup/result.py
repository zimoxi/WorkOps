"""
WorkOps Production Backup Result — 生产备份结果
Sprint061: Production Backup Execution Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import ProductionBackupStatus
from .errors import InvalidProductionBackupRequestError


@dataclass(frozen=True, slots=True)
class ProductionBackupResult:
    """
    生产备份结果。不可变。
    """

    backup_id: str
    status: ProductionBackupStatus
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidProductionBackupRequestError("backup_id must be a non-empty string")
        if not isinstance(self.status, ProductionBackupStatus):
            raise InvalidProductionBackupRequestError("status must be a ProductionBackupStatus instance")
        if not isinstance(self.success, bool):
            raise InvalidProductionBackupRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidProductionBackupRequestError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
