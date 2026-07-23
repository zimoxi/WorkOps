"""
WorkOps Restore Executor Contract — 恢复执行器接口
Sprint037: Restore Execution Framework

定义恢复执行器接口。不实现真实恢复。
"""

from abc import ABC, abstractmethod

from .execution import RestoreExecution
from .result import RestoreResult


class RestoreExecutor(ABC):
    """
    恢复执行器接口。

    只定义接口。不实现真实恢复。
    """

    @abstractmethod
    def execute(self, execution: RestoreExecution) -> RestoreResult:
        """
        执行恢复。

        Args:
            execution: 恢复执行记录

        Returns:
            RestoreResult
        """
        ...
