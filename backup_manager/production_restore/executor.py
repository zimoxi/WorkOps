"""
WorkOps Production Restore Executor Contract — 生产恢复执行器接口
Sprint062: Production Restore Execution Foundation

只定义接口。不实现真实恢复。
"""

from abc import ABC, abstractmethod

from .model import ProductionRestoreRequest
from .result import ProductionRestoreResult


class ProductionRestoreExecutor(ABC):
    """
    生产恢复执行器接口。

    执行顺序：
    Validate Request → Create Execution Context → Validate Security Boundary → Dispatch Runtime → Return Result

    只定义接口。不实现真实恢复。
    """

    @abstractmethod
    def execute(self, request: ProductionRestoreRequest) -> ProductionRestoreResult:
        """
        执行生产恢复。

        Args:
            request: 生产恢复请求

        Returns:
            ProductionRestoreResult
        """
        ...
