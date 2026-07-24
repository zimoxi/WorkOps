"""
WorkOps PVE API Connector Contract — PVE API 连接器接口
Sprint059: PVE API Runtime Foundation

只定义接口。不实现真实 API 连接。
"""

from abc import ABC, abstractmethod

from .model import PVERuntimeSession
from .request import PVEAPIRequest
from .result import PVERuntimeResult


class PVEAPIConnector(ABC):
    """
    PVE API 连接器接口。

    只定义接口。不实现真实 API 连接。
    """

    @abstractmethod
    def connect(self, session: PVERuntimeSession) -> None:
        """
        建立 PVE API 连接。

        Args:
            session: PVE 运行时会话
        """
        ...

    @abstractmethod
    def execute_readonly(self, request: PVEAPIRequest) -> PVERuntimeResult:
        """
        执行只读 PVE API 请求。

        Args:
            request: PVE API 请求

        Returns:
            PVERuntimeResult
        """
        ...
