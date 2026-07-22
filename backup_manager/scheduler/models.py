"""
WorkOps Backup Schedule Binding — 调度绑定模型
Sprint035: Backup Scheduler Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidScheduleError


@dataclass(frozen=True, slots=True)
class BackupScheduleBinding:
    """
    调度绑定。不可变。

    绑定 job_id 和 cron_expression。
    """

    binding_id: str
    job_id: str
    cron_expression: str
    enabled: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.binding_id, str) or not self.binding_id.strip():
            raise InvalidScheduleError("binding_id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidScheduleError("job_id must be a non-empty string")
        if not isinstance(self.cron_expression, str) or not self.cron_expression.strip():
            raise InvalidScheduleError("cron_expression must be a non-empty string")
        if not isinstance(self.enabled, bool):
            raise InvalidScheduleError("enabled must be a bool")
        # created_at 在 frozen dataclass 中不能用 default_factory
        # 所以在 __post_init__ 中处理
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
