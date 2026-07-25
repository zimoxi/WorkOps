"""
WorkOps Production Restore Model — 生产恢复模型
Sprint062: Production Restore Execution Foundation

ProductionRestoreStatus, ProductionRestoreRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidProductionRestoreRequestError


class ProductionRestoreStatus(Enum):
    """生产恢复状态。"""

    CREATED = "created"
    VALIDATING = "validating"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ProductionRestoreRequest:
    """
    生产恢复请求。不可变。
    """

    restore_id: str
    backup_id: str
    execution_id: str
    transaction_id: str
    adapter_id: str
    runtime_type: str
    created_at: datetime = None

    def __post_init__(self):
        for field_name in ["restore_id", "backup_id", "execution_id", "transaction_id", "adapter_id", "runtime_type"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidProductionRestoreRequestError(f"{field_name} must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_production_restore_request(request: ProductionRestoreRequest) -> None:
    """
    验证生产恢复请求。

    Args:
        request: 生产恢复请求

    Raises:
        InvalidProductionRestoreRequestError: 验证失败
    """
    if not isinstance(request, ProductionRestoreRequest):
        raise InvalidProductionRestoreRequestError("request must be a ProductionRestoreRequest instance")
