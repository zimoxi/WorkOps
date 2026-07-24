"""
WorkOps Backup Runtime Dispatcher Contract — 备份运行时分发器接口
Sprint061: Production Backup Execution Foundation

只定义接口。不实现真实分发。
"""

from abc import ABC, abstractmethod

from .model import ProductionBackupRequest
from .result import ProductionBackupResult


class BackupRuntimeDispatcher(ABC):
    """
    备份运行时分发器接口。

    路由备份请求到 Linux/PVE/OMV 运行时。

    只定义接口。不实现真实分发。
    """

    @abstractmethod
    def dispatch(self, request: ProductionBackupRequest) -> ProductionBackupResult:
        """
        分发备份请求。

        Args:
            request: 生产备份请求

        Returns:
            ProductionBackupResult
        """
        ...
