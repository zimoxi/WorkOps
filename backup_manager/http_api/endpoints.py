"""
WorkOps HTTP Endpoints — HTTP 端点契约
Sprint066: HTTP API Runtime Foundation

只定义接口。不实现业务逻辑。
"""

from abc import ABC, abstractmethod

from .models import HTTPRequest, HTTPResponse


class HealthEndpoint(ABC):
    """健康检查端点接口。"""

    @abstractmethod
    def handle(self, request: HTTPRequest) -> HTTPResponse:
        """
        处理健康检查请求。

        Args:
            request: HTTP 请求

        Returns:
            HTTPResponse
        """
        ...


class BackupEndpoint(ABC):
    """备份端点接口。"""

    @abstractmethod
    def handle(self, request: HTTPRequest) -> HTTPResponse:
        """
        处理备份请求。

        Args:
            request: HTTP 请求

        Returns:
            HTTPResponse
        """
        ...


class RestoreEndpoint(ABC):
    """恢复端点接口。"""

    @abstractmethod
    def handle(self, request: HTTPRequest) -> HTTPResponse:
        """
        处理恢复请求。

        Args:
            request: HTTP 请求

        Returns:
            HTTPResponse
        """
        ...


class StatusEndpoint(ABC):
    """状态端点接口。"""

    @abstractmethod
    def handle(self, request: HTTPRequest) -> HTTPResponse:
        """
        处理状态请求。

        Args:
            request: HTTP 请求

        Returns:
            HTTPResponse
        """
        ...
