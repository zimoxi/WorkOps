"""
WorkOps Backup Engine Model — 备份引擎模型
Sprint070: Real Backup Execution Engine

BackupExecutionMode, BackupExecutionRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidBackupExecutionError


class BackupExecutionMode(Enum):
    """备份执行模式。"""

    LINUX = "linux"
    PVE = "pve"
    OMV = "omv"


@dataclass(frozen=True, slots=True)
class BackupExecutionRequest:
    """
    备份执行请求。不可变。
    """

    backup_id: str
    execution_id: str
    transaction_id: str
    adapter_id: str
    mode: BackupExecutionMode
    created_at: datetime = None

    def __post_init__(self):
        for field_name in ["backup_id", "execution_id", "transaction_id", "adapter_id"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidBackupExecutionError(f"{field_name} must be a non-empty string")
        if not isinstance(self.mode, BackupExecutionMode):
            raise InvalidBackupExecutionError("mode must be a BackupExecutionMode instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
