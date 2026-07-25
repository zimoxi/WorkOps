"""
WorkOps Operation Service Contract — 操作服务接口
Sprint064: API Service Layer Foundation

只定义接口。不实现 HTTP 服务。
"""

from abc import ABC, abstractmethod

from .v1_request import APIRequest
from .v1_response import APIResponse


class OperationService(ABC):
    """
    操作服务接口。

    桥接 API 层到内部操作。

    只定义接口。不实现 HTTP 服务。
    """

    @abstractmethod
    def handle(self, request: APIRequest) -> APIResponse:
        """
        处理 API 请求。

        Args:
            request: API 请求

        Returns:
            APIResponse
        """
        ...
