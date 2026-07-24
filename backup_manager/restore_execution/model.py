"""
WorkOps Restore Execution Model — 恢复执行模型
Sprint054: Restore Execution Pipeline Foundation

RestoreExecutionStatus, RestoreExecutionRequest
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidRestoreExecutionRequestError


class RestoreExecutionStatus(Enum):
    """恢复执行状态。"""

    CREATED = "created"
    PREPARING = "preparing"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class RestoreExecutionRequest:
    """
    恢复执行请求。不可变。
    """

    restore_id: str
    operation_id: str
    job_id: str
    execution_id: str
    adapter_id: str
    backup_id: str
    created_at: datetime = None

    def __post_init__(self):
        for field_name in ["restore_id", "operation_id", "job_id", "execution_id", "adapter_id", "backup_id"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidRestoreExecutionRequestError(f"{field_name} must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_restore_execution_request(request: RestoreExecutionRequest) -> None:
    """
    验证恢复执行请求。

    Args:
        request: 恢复执行请求

    Raises:
        InvalidRestoreExecutionRequestError: 验证失败
    """
    if not isinstance(request, RestoreExecutionRequest):
        raise InvalidRestoreExecutionRequestError("request must be a RestoreExecutionRequest instance")
