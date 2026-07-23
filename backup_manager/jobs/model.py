"""
WorkOps Job Model — 作业模型
Sprint039: Job Scheduler Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .status import JobType
from .errors import InvalidJobError


class JobStatus:
    """作业状态常量。"""

    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

    _VALID = {"created", "queued", "running", "success", "failed", "cancelled"}

    @classmethod
    def validate(cls, value: str) -> str:
        if value not in cls._VALID:
            raise InvalidJobError(f"Invalid job status: {value}")
        return value


@dataclass(frozen=True, slots=True)
class Job:
    """
    作业。不可变。
    """

    job_id: str
    job_type: JobType
    operation_id: str
    status: str = JobStatus.CREATED
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidJobError("job_id must be a non-empty string")
        if not isinstance(self.job_type, JobType):
            raise InvalidJobError("job_type must be a JobType instance")
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidJobError("operation_id must be a non-empty string")
        JobStatus.validate(self.status)
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
