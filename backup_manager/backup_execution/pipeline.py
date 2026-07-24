"""
WorkOps Backup Execution Pipeline — 备份执行管道
Sprint053: Backup Execution Pipeline Foundation

只定义接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .model import BackupExecutionRequest
from .result import BackupExecutionResult


class BackupExecutionPipeline(ABC):
    """
    备份执行管道接口。

    协调：Backup Request → Execution Context → Runtime Connector → Backup Result

    只定义接口。不实现真实执行。
    """

    @abstractmethod
    def prepare(self, request: BackupExecutionRequest) -> None:
        """
        准备备份执行。

        Args:
            request: 备份执行请求
        """
        ...

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
