"""
WorkOps Health Executor Contract — 健康执行器接口
Sprint055: Health Runtime Integration Foundation

只定义接口。不实现真实监控。
"""

from abc import ABC, abstractmethod

from .request import HealthExecutionRequest
from .result import HealthExecutionResult


class HealthExecutor(ABC):
    """
    健康执行器接口。

    只定义接口。不实现真实监控。
    """

    @abstractmethod
    def execute(self, request: HealthExecutionRequest) -> HealthExecutionResult:
        """
        执行健康检查。

        Args:
            request: 健康执行请求

        Returns:
            HealthExecutionResult
        """
        ...
