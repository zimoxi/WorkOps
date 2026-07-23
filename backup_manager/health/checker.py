"""
WorkOps Health Checker Contract — 健康检查器接口
Sprint043: Device Health Monitoring Foundation

只定义接口。不实现真实检查。
"""

from abc import ABC, abstractmethod

from .request import HealthCheckRequest
from .result import HealthResult


class HealthChecker(ABC):
    """
    健康检查器接口。

    只定义接口。不实现真实检查。
    """

    @abstractmethod
    def check(self, request: HealthCheckRequest) -> HealthResult:
        """
        执行健康检查。

        Args:
            request: 健康检查请求

        Returns:
            HealthResult
        """
        ...
