"""
WorkOps Job History — 作业历史模型
Sprint039: Job Scheduler Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .model import JobStatus
from .errors import InvalidJobError


@dataclass(frozen=True, slots=True)
class JobHistory:
    """
    作业历史记录。不可变。
    """

    job_id: str
    status: str
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidJobError("job_id must be a non-empty string")
        JobStatus.validate(self.status)
        now = datetime.now(timezone.utc)
        if self.created_at is None:
            object.__setattr__(self, "created_at", now)
        if self.updated_at is None:
            object.__setattr__(self, "updated_at", now)
