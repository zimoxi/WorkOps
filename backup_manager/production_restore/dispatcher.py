"""
WorkOps Restore Runtime Dispatcher Contract — 恢复运行时分发器接口
Sprint062: Production Restore Execution Foundation

只定义接口。不实现真实分发。
"""

from abc import ABC, abstractmethod

from .model import ProductionRestoreRequest
from .result import ProductionRestoreResult


class RestoreRuntimeDispatcher(ABC):
    """
    恢复运行时分发器接口。

    路由恢复请求到 Linux/PVE/OMV 运行时。

    只定义接口。不实现真实分发。
    """

    @abstractmethod
    def dispatch(self, request: ProductionRestoreRequest) -> ProductionRestoreResult:
        """
        分发恢复请求。

        Args:
            request: 生产恢复请求

        Returns:
            ProductionRestoreResult
        """
        ...
