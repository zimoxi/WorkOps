"""
WorkOps Production Backup Model — 生产备份模型
Sprint061: Production Backup Execution Foundation

ProductionBackupStatus, ProductionBackupRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidProductionBackupRequestError


class ProductionBackupStatus(Enum):
    """生产备份状态。"""

    CREATED = "created"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProductionBackupRequest:
    """
    生产备份请求。不可变。
    """

    backup_id: str
    execution_id: str
    transaction_id: str
    adapter_id: str
    runtime_type: str
    created_at: datetime = None

    def __post_init__(self):
        for field_name in ["backup_id", "execution_id", "transaction_id", "adapter_id", "runtime_type"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidProductionBackupRequestError(f"{field_name} must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_production_backup_request(request: ProductionBackupRequest) -> None:
    """
    验证生产备份请求。

    Args:
        request: 生产备份请求

    Raises:
        InvalidProductionBackupRequestError: 验证失败
    """
    if not isinstance(request, ProductionBackupRequest):
        raise InvalidProductionBackupRequestError("request must be a ProductionBackupRequest instance")
