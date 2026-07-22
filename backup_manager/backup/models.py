"""
WorkOps Backup Job Model — 备份任务模型
Sprint029: Backup Workflow Foundation

frozen dataclass。不包含任何 credential/connection 信息。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .errors import InvalidBackupJobError


@dataclass(frozen=True, slots=True)
class BackupJob:
    """
    备份任务。不可变。

    只描述任务元数据，不包含任何连接/认证信息。
    """

    job_id: str
    name: str
    source_device_id: str
    target_device_id: str
    schedule_id: str
    policy_id: str
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidBackupJobError("job_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidBackupJobError("name must be a non-empty string")
        if not isinstance(self.source_device_id, str) or not self.source_device_id.strip():
            raise InvalidBackupJobError("source_device_id must be a non-empty string")
        if not isinstance(self.target_device_id, str) or not self.target_device_id.strip():
            raise InvalidBackupJobError("target_device_id must be a non-empty string")
        if not isinstance(self.schedule_id, str) or not self.schedule_id.strip():
            raise InvalidBackupJobError("schedule_id must be a non-empty string")
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise InvalidBackupJobError("policy_id must be a non-empty string")
        if not isinstance(self.enabled, bool):
            raise InvalidBackupJobError("enabled must be a bool")
