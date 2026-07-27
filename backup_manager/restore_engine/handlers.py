"""
WorkOps Restore Runtime Handlers — 恢复运行时处理器
Sprint071: Real Restore Execution Engine

Only contracts. No actual overwrite. No data mutation.
"""

from abc import ABC, abstractmethod

from .model import RestoreExecutionRequest
from .result import RestoreExecutionResult


class LinuxRestoreHandler(ABC):
    """Linux 恢复处理器接口。"""

    @abstractmethod
    def execute(self, request: RestoreExecutionRequest) -> RestoreExecutionResult:
        """
        执行 Linux 恢复。

        Args:
            request: 恢复执行请求

        Returns:
            RestoreExecutionResult
        """
        ...


class PVERestoreHandler(ABC):
    """PVE 恢复处理器接口。"""

    @abstractmethod
    def execute(self, request: RestoreExecutionRequest) -> RestoreExecutionResult:
        """
        执行 PVE 恢复。

        Args:
            request: 恢复执行请求

        Returns:
            RestoreExecutionResult
        """
        ...


class OMVRestoreHandler(ABC):
    """OMV 恢复处理器接口。"""

    @abstractmethod
    def execute(self, request: RestoreExecutionRequest) -> RestoreExecutionResult:
        """
        执行 OMV 恢复。

        Args:
            request: 恢复执行请求

        Returns:
            RestoreExecutionResult
        """
        ...
