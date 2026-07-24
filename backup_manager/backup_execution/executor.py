"""
WorkOps Backup Executor Contract — 备份执行器接口
Sprint053: Backup Execution Pipeline Foundation

只定义接口。不实现真实备份。
"""

from abc import ABC, abstractmethod

from .model import BackupExecutionRequest
from .result import BackupExecutionResult


class BackupExecutor(ABC):
    """
    备份执行器接口。

    只定义接口。不实现真实备份。
    """

    @abstractmethod
    def execute(self, request: BackupExecutionRequest) -> BackupExecutionResult:
        """
        执行备份。

        Args:
            request: 备份执行请求

        Returns:
            BackupExecutionResult
        """
        ...
