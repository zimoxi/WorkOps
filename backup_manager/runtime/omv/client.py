"""
WorkOps OMV API Client Contract — OMV API 客户端接口
Sprint069: Real OMV API Client

只定义接口。不绑定 requests/aiohttp/httpx。
"""

from abc import ABC, abstractmethod

from .connection import OMVConnectionConfig


class OMVAPIClient(ABC):
    """
    OMV API 客户端接口。

    允许未来实现:
    - requests
    - aiohttp
    - httpx

    不硬编码库依赖。
    """

    @abstractmethod
    def connect(self, config: OMVConnectionConfig) -> None:
        """
        建立 OMV API 连接。

        Args:
            config: OMV 连接配置
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """关闭 OMV API 连接。"""
        ...
