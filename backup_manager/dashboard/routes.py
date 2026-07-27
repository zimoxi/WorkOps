"""
WorkOps Dashboard Routes Contract — 仪表盘路由接口
Sprint073: Web Dashboard Foundation

只定义接口。不实现 HTTP 路由。
"""

from abc import ABC, abstractmethod


class DashboardRoutes(ABC):
    """
    仪表盘路由接口。

    Routes:
        /
        /overview
        /runtime
        /backup
        /restore
        /health
        /metrics
        /audit

    只定义接口。不实现 HTTP 路由。
    """

    @abstractmethod
    def register_routes(self) -> None:
        """注册路由。"""
        ...
