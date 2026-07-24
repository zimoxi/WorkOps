"""
WorkOps ReadOnly Runtime Connector Contract — 只读运行时连接器接口
Sprint052: ReadOnly Runtime Connector Foundation

只定义接口。不实现真实连接。
"""

from abc import ABC, abstractmethod

from .request import RuntimeRequest
from .result import RuntimeResult


class ReadOnlyRuntimeConnector(ABC):
    """
    只读运行时连接器接口。

    只定义接口。不实现真实连接。
    """

    @abstractmethod
    def execute(self, request: RuntimeRequest) -> RuntimeResult:
        """
        执行只读运行时请求。

        Args:
            request: 运行时请求

        Returns:
            RuntimeResult
        """
        ...
