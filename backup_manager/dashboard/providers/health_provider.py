"""
WorkOps Health Dashboard Provider — 健康仪表盘数据提供者
Sprint075: Dashboard Runtime Integration

Returns health summary: system state, runtime availability.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HealthSummary:
    """
    健康摘要。不可变。
    """

    system_state: str
    runtime_available: bool
    message: str


class HealthDashboardProvider(ABC):
    """
    健康仪表盘数据提供者接口。

    返回: HealthSummary
    """

    @abstractmethod
    def get_health_summary(self) -> HealthSummary:
        """
        获取健康摘要。

        Returns:
            HealthSummary
        """
        ...
