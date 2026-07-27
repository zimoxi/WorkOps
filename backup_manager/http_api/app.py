"""
WorkOps HTTP Application Contract — HTTP 应用接口
Sprint066: HTTP API Runtime Foundation

只定义接口。不实现真实 HTTP 服务。
"""

from abc import ABC, abstractmethod


class HTTPApplication(ABC):
    """
    HTTP 应用接口。

    只定义接口。不实现真实 HTTP 服务。
    """

    @abstractmethod
    def create_app(self):
        """
        创建 HTTP 应用。

        Returns:
            HTTP Application instance
        """
        ...
