"""
WorkOps Operation Gateway Contract — 操作网关接口
Sprint045: Unified Operation API Foundation

只定义接口。不实现 HTTP/REST。
"""

from abc import ABC, abstractmethod

from .request import OperationRequestModel
from .response import OperationResponseModel


class OperationGateway(ABC):
    """
    操作网关接口。

    只定义接口。不实现 HTTP/REST。
    """

    @abstractmethod
    def submit(self, request: OperationRequestModel) -> OperationResponseModel:
        """
        提交操作请求。

        Args:
            request: 操作请求

        Returns:
            OperationResponseModel
        """
        ...
