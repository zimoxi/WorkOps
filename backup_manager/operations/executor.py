"""
WorkOps Operation Executor Contract — 操作执行器接口
Sprint038: Operation Orchestration Foundation

只定义接口。不执行真实操作。
"""

from abc import ABC, abstractmethod

from .model import OperationRequest
from .result import OperationResult


class OperationExecutor(ABC):
    """
    操作执行器接口。

    只定义接口。不执行真实操作。
    """

    @abstractmethod
    def execute(self, request: OperationRequest) -> OperationResult:
        """
        执行操作。

        Args:
            request: 操作请求

        Returns:
            OperationResult
        """
        ...
