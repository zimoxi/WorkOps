"""
WorkOps Backup Runtime Handlers — 备份运行时处理器
Sprint070: Real Backup Execution Engine

Only contracts. No actual data copy.
"""

from abc import ABC, abstractmethod

from .model import BackupExecutionRequest
from .result import BackupExecutionResult


class LinuxBackupHandler(ABC):
    """Linux 备份处理器接口。"""

    @abstractmethod
    def execute(self, request: BackupExecutionRequest) -> BackupExecutionResult:
        """
        执行 Linux 备份。

        Args:
            request: 备份执行请求

        Returns:
            BackupExecutionResult
        """
        ...


class PVEBackupHandler(ABC):
    """PVE 备份处理器接口。"""

    @abstractmethod
    def execute(self, request: BackupExecutionRequest) -> BackupExecutionResult:
        """
        执行 PVE 备份。

        Args:
            request: 备份执行请求

        Returns:
            BackupExecutionResult
        """
        ...


class OMVBackupHandler(ABC):
    """OMV 备份处理器接口。"""

    @abstractmethod
    def execute(self, request: BackupExecutionRequest) -> BackupExecutionResult:
        """
        执行 OMV 备份。

        Args:
            request: 备份执行请求

        Returns:
            BackupExecutionResult
        """
        ...
