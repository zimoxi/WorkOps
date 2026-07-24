"""
WorkOps Restore Execution Pipeline — 恢复执行管道
Sprint054: Restore Execution Pipeline Foundation

只定义接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .model import RestoreExecutionRequest
from .result import RestoreExecutionResult


class RestoreExecutionPipeline(ABC):
    """
    恢复执行管道接口。

    协调：Restore Request → Execution Context → Runtime Connector → Restore Result

    只定义接口。不实现真实执行。
    """

    @abstractmethod
    def prepare(self, request: RestoreExecutionRequest) -> None:
        """
        准备恢复执行。

        Args:
            request: 恢复执行请求
        """
        ...

    @abstractmethod
    def execute(self, request: RestoreExecutionRequest) -> RestoreExecutionResult:
        """
        执行恢复。

        Args:
            request: 恢复执行请求

        Returns:
            RestoreExecutionResult
        """
        ...
