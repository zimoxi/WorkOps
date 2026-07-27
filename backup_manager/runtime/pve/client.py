"""
WorkOps PVE API Client Contract — PVE API 客户端接口
Sprint068: Real PVE API Client

只定义接口。不绑定 requests/aiohttp/httpx。
"""

from abc import ABC, abstractmethod

from .connection import PVEConnectionConfig


class PVEAPIClient(ABC):
    """
    PVE API 客户端接口。

    允许未来实现:
    - requests
    - aiohttp
    - httpx

    不硬编码库依赖。
    """

    @abstractmethod
    def connect(self, config: PVEConnectionConfig) -> None:
        """
        建立 PVE API 连接。

        Args:
            config: PVE 连接配置
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """关闭 PVE API 连接。"""
        ...
