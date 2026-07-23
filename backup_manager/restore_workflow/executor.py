"""
WorkOps Restore Workflow Executor Contract — 恢复工作流执行器接口
Sprint042: Restore Workflow Foundation v1

只定义接口。不执行真实恢复。
"""

from abc import ABC, abstractmethod

from .request import RestoreRequest
from .result import RestoreResult


class RestoreWorkflowExecutor(ABC):
    """
    恢复工作流执行器接口。

    只定义接口。不执行真实恢复。
    """

    @abstractmethod
    def execute(self, request: RestoreRequest) -> RestoreResult:
        """
        执行恢复。

        Args:
            request: 恢复请求

        Returns:
            RestoreResult
        """
        ...
