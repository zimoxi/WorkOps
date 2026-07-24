"""
WorkOps Backup Execution Model — 备份执行模型
Sprint053: Backup Execution Pipeline Foundation

BackupExecutionStatus, BackupExecutionRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidBackupExecutionRequestError


class BackupExecutionStatus(Enum):
    """备份执行状态。"""

    CREATED = "created"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class BackupExecutionRequest:
    """
    备份执行请求。不可变。
    """

    backup_id: str
    operation_id: str
    job_id: str
    execution_id: str
    adapter_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.backup_id, str) or not self.backup_id.strip():
            raise InvalidBackupExecutionRequestError("backup_id must be a non-empty string")
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidBackupExecutionRequestError("operation_id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidBackupExecutionRequestError("job_id must be a non-empty string")
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise InvalidBackupExecutionRequestError("execution_id must be a non-empty string")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidBackupExecutionRequestError("adapter_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_backup_execution_request(request: BackupExecutionRequest) -> None:
    """
    验证备份执行请求。

    Args:
        request: 备份执行请求

    Raises:
        InvalidBackupExecutionRequestError: 验证失败
    """
    if not isinstance(request, BackupExecutionRequest):
        raise InvalidBackupExecutionRequestError("request must be a BackupExecutionRequest instance")
