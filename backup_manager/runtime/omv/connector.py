"""
WorkOps OMV API Connector Contract — OMV API 连接器接口
Sprint060: OMV API Runtime Foundation

只定义接口。不实现真实 API 连接。
"""

from abc import ABC, abstractmethod

from .model import OMVRuntimeSession
from .request import OMVAPIRequest
from .result import OMVRuntimeResult


class OMVAPIConnector(ABC):
    """
    OMV API 连接器接口。

    只定义接口。不实现真实 API 连接。
    """

    @abstractmethod
    def connect(self, session: OMVRuntimeSession) -> None:
        """
        建立 OMV API 连接。

        Args:
            session: OMV 运行时会话
        """
        ...

    @abstractmethod
    def execute_readonly(self, request: OMVAPIRequest) -> OMVRuntimeResult:
        """
        执行只读 OMV API 请求。

        Args:
            request: OMV API 请求

        Returns:
            OMVRuntimeResult
        """
        ...
