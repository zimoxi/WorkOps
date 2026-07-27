"""
WorkOps HTTP Middleware — HTTP 中间件
Sprint066: HTTP API Runtime Foundation

SecurityMiddleware contract.
"""

from abc import ABC, abstractmethod

from .models import HTTPRequest


class SecurityMiddleware(ABC):
    """
    安全中间件接口。

    只定义接口。不实现认证。
    """

    @abstractmethod
    def process(self, request: HTTPRequest) -> HTTPRequest:
        """
        处理安全检查。

        Args:
            request: HTTP 请求

        Returns:
            HTTPRequest (possibly modified)
        """
        ...
