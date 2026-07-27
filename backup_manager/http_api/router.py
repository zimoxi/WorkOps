"""
WorkOps API Router Contract — API 路由接口
Sprint066: HTTP API Runtime Foundation

只定义接口。不实现真实路由。
"""

from abc import ABC, abstractmethod


class APIRouter(ABC):
    """
    API 路由接口。

    只定义接口。不实现真实路由。
    """

    @abstractmethod
    def register_routes(self) -> None:
        """
        注册路由。

        Routes:
            /health
            /status
            /backup
            /restore
        """
        ...
