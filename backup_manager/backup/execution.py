"""
WorkOps Backup Execution Model — 备份执行模型
Sprint030: Backup Execution Engine

frozen dataclass。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .state import BackupExecutionState
from .errors import BackupExecutionError


@dataclass(frozen=True, slots=True)
class BackupExecution:
    """
    备份执行记录。不可变。
    """

    execution_id: str
    job_id: str
    state: BackupExecutionState = BackupExecutionState.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str = ""

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise BackupExecutionError("execution_id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise BackupExecutionError("job_id must be a non-empty string")
        if not isinstance(self.state, BackupExecutionState):
            raise BackupExecutionError("state must be a BackupExecutionState instance")
        if self.started_at is not None and not isinstance(self.started_at, datetime):
            raise BackupExecutionError("started_at must be a datetime or None")
        if self.finished_at is not None and not isinstance(self.finished_at, datetime):
            raise BackupExecutionError("finished_at must be a datetime or None")
        if not isinstance(self.message, str):
            raise BackupExecutionError("message must be a string")
