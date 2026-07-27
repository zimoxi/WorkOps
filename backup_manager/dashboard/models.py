"""
WorkOps Dashboard Models — 仪表盘模型
Sprint073: Web Dashboard Foundation

DashboardStatus, DashboardViewModel, RuntimeOverview,
BackupOverview, RestoreOverview
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidDashboardRequestError


class DashboardStatus(Enum):
    """仪表盘状态。"""

    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class DashboardViewModel:
    """
    仪表盘视图模型。不可变。
    """

    system_name: str
    status: DashboardStatus
    runtime_count: int
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.system_name, str) or not self.system_name.strip():
            raise InvalidDashboardRequestError("system_name must be a non-empty string")
        if not isinstance(self.status, DashboardStatus):
            raise InvalidDashboardRequestError("status must be a DashboardStatus instance")
        if not isinstance(self.runtime_count, int) or self.runtime_count < 0:
            raise InvalidDashboardRequestError("runtime_count must be a non-negative integer")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class RuntimeOverview:
    """
    运行时概览。不可变。
    """

    runtime_name: str
    connected: bool
    message: str

    def __post_init__(self):
        if not isinstance(self.runtime_name, str) or not self.runtime_name.strip():
            raise InvalidDashboardRequestError("runtime_name must be a non-empty string")
        if not isinstance(self.connected, bool):
            raise InvalidDashboardRequestError("connected must be a bool")
        if not isinstance(self.message, str):
            raise InvalidDashboardRequestError("message must be a string")


@dataclass(frozen=True, slots=True)
class BackupOverview:
    """
    备份概览。不可变。
    """

    total: int
    successful: int
    failed: int

    def __post_init__(self):
        for field_name in ["total", "successful", "failed"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise InvalidDashboardRequestError(f"{field_name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class RestoreOverview:
    """
    恢复概览。不可变。
    """

    total: int
    successful: int
    failed: int

    def __post_init__(self):
        for field_name in ["total", "successful", "failed"]:
            value = getattr(self, field_name)
            if not isinstance(value, int) or value < 0:
                raise InvalidDashboardRequestError(f"{field_name} must be a non-negative integer")
