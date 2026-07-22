"""
WorkOps Executor Result — 执行结果模型
Sprint031: Backup Executor Framework

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime

from .errors import BackupExecutorError


@dataclass(frozen=True, slots=True)
class ExecutorResult:
    """
    执行结果。不可变。
    """

    success: bool
    message: str
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def __post_init__(self):
        if not isinstance(self.success, bool):
            raise BackupExecutorError("success must be a bool")
        if not isinstance(self.message, str):
            raise BackupExecutorError("message must be a str")
        if self.started_at is not None and not isinstance(self.started_at, datetime):
            raise BackupExecutorError("started_at must be a datetime or None")
        if self.finished_at is not None and not isinstance(self.finished_at, datetime):
            raise BackupExecutorError("finished_at must be a datetime or None")
