"""
WorkOps Restore Engine Model — 恢复引擎模型
Sprint071: Real Restore Execution Engine

RestoreExecutionMode, RestoreExecutionRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidRestoreExecutionError


class RestoreExecutionMode(Enum):
    """恢复执行模式。"""

    LINUX = "linux"
    PVE = "pve"
    OMV = "omv"


@dataclass(frozen=True, slots=True)
class RestoreExecutionRequest:
    """
    恢复执行请求。不可变。
    """

    restore_id: str
    backup_id: str
    execution_id: str
    transaction_id: str
    adapter_id: str
    mode: RestoreExecutionMode
    created_at: datetime = None

    def __post_init__(self):
        for field_name in ["restore_id", "backup_id", "execution_id", "transaction_id", "adapter_id"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidRestoreExecutionError(f"{field_name} must be a non-empty string")
        if not isinstance(self.mode, RestoreExecutionMode):
            raise InvalidRestoreExecutionError("mode must be a RestoreExecutionMode instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
