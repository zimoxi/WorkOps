"""
WorkOps Scheduler Trigger — 调度触发器
Sprint035: Backup Scheduler Foundation

frozen dataclass。
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidScheduleError


@dataclass(frozen=True, slots=True)
class SchedulerTrigger:
    """
    调度触发器。不可变。
    """

    trigger_id: str
    binding_id: str
    trigger_time: datetime

    def __post_init__(self):
        if not isinstance(self.trigger_id, str) or not self.trigger_id.strip():
            raise InvalidScheduleError("trigger_id must be a non-empty string")
        if not isinstance(self.binding_id, str) or not self.binding_id.strip():
            raise InvalidScheduleError("binding_id must be a non-empty string")
        if not isinstance(self.trigger_time, datetime):
            raise InvalidScheduleError("trigger_time must be a datetime")

    @classmethod
    def create(cls, binding_id: str) -> "SchedulerTrigger":
        """创建触发器。"""
        return cls(
            trigger_id=uuid.uuid4().hex,
            binding_id=binding_id,
            trigger_time=datetime.now(timezone.utc),
        )
