"""
WorkOps Metrics Collector Contract — 指标收集器接口
Sprint063: Monitoring Metrics Foundation

只定义接口。不实现真实收集。
"""

from abc import ABC, abstractmethod

from .model import MetricRecord


class MetricsCollector(ABC):
    """
    指标收集器接口。

    只定义接口。不实现真实收集。
    """

    @abstractmethod
    def collect(self, record: MetricRecord) -> None:
        """
        收集指标记录。

        Args:
            record: 指标记录
        """
        ...
