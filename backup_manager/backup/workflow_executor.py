"""
WorkOps Backup Workflow Executor Contract — 备份工作流执行器接口
Sprint041: Backup Workflow Foundation v1

只定义接口。不执行真实备份。
"""

from abc import ABC, abstractmethod

from .workflow_request import BackupRequest
from .workflow_result import BackupResult


class BackupWorkflowExecutor(ABC):
    """
    备份工作流执行器接口。

    只定义接口。不执行真实备份。
    """

    @abstractmethod
    def execute(self, request: BackupRequest) -> BackupResult:
        """
        执行备份。

        Args:
            request: 备份请求

        Returns:
            BackupResult
        """
        ...
