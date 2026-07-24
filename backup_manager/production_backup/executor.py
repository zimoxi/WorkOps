"""
WorkOps Production Backup Executor Contract — 生产备份执行器接口
Sprint061: Production Backup Execution Foundation

只定义接口。不实现真实备份。
"""

from abc import ABC, abstractmethod

from .model import ProductionBackupRequest
from .result import ProductionBackupResult


class ProductionBackupExecutor(ABC):
    """
    生产备份执行器接口。

    执行顺序：
    Validate Request → Create Execution Context → Validate Security Boundary → Dispatch Runtime → Return Result

    只定义接口。不实现真实备份。
    """

    @abstractmethod
    def execute(self, request: ProductionBackupRequest) -> ProductionBackupResult:
        """
        执行生产备份。

        Args:
            request: 生产备份请求

        Returns:
            ProductionBackupResult
        """
        ...
