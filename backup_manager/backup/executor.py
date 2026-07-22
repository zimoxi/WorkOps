"""
WorkOps Backup Executor Contract — 备份执行器接口
Sprint031: Backup Executor Framework

定义备份执行器接口。不实现真实备份。
"""

from abc import ABC, abstractmethod

from .execution import BackupExecution
from .executor_result import ExecutorResult


class BackupExecutor(ABC):
    """
    备份执行器接口。

    只定义接口。不实现真实备份。
    """

    @abstractmethod
    def execute(self, execution: BackupExecution) -> ExecutorResult:
        """
        执行备份。

        Args:
            execution: 执行记录

        Returns:
            ExecutorResult
        """
        ...
