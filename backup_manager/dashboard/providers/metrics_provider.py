"""
WorkOps Metrics Dashboard Provider — 指标仪表盘数据提供者
Sprint075: Dashboard Runtime Integration

Returns metrics summary: operation count, runtime statistics.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MetricsSummary:
    """
    指标摘要。不可变。
    """

    operation_count: int
    runtime_count: int
    message: str


class MetricsDashboardProvider(ABC):
    """
    指标仪表盘数据提供者接口。

    返回: MetricsSummary
    """

    @abstractmethod
    def get_metrics_summary(self) -> MetricsSummary:
        """
        获取指标摘要。

        Returns:
            MetricsSummary
        """
        ...
