"""
WorkOps Restore Result — 恢复结果模型
Sprint037: Restore Execution Framework

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime

from .errors import RestoreExecutorError


@dataclass(frozen=True, slots=True)
class RestoreResult:
    """
    恢复结果。不可变。
    """

    success: bool
    message: str
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def __post_init__(self):
        if not isinstance(self.success, bool):
            raise RestoreExecutorError("success must be a bool")
        if not isinstance(self.message, str):
            raise RestoreExecutorError("message must be a str")
        if self.started_at is not None and not isinstance(self.started_at, datetime):
            raise RestoreExecutorError("started_at must be a datetime or None")
        if self.finished_at is not None and not isinstance(self.finished_at, datetime):
            raise RestoreExecutorError("finished_at must be a datetime or None")
