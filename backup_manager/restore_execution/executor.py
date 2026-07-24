"""
WorkOps Restore Executor Contract — 恢复执行器接口
Sprint054: Restore Execution Pipeline Foundation

只定义接口。不实现真实恢复。
"""

from abc import ABC, abstractmethod

from .model import RestoreExecutionRequest
from .result import RestoreExecutionResult


class RestoreExecutor(ABC):
    """
    恢复执行器接口。

    只定义接口。不实现真实恢复。
    """

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
