"""
WorkOps Metrics Query Service Contract — 指标查询服务接口
Sprint063: Monitoring Metrics Foundation

只定义接口。不实现存储。
"""

from abc import ABC, abstractmethod

from .model import MetricRecord, MetricQuery


class MetricsQueryService(ABC):
    """
    指标查询服务接口。

    只定义接口。不实现存储。
    """

    @abstractmethod
    def query(self, query: MetricQuery) -> list:
        """
        查询指标记录。

        Args:
            query: 指标查询

        Returns:
            list[MetricRecord]
        """
        ...
