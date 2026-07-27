"""
WorkOps Dashboard Routes — 仪表盘路由
Sprint073/Sprint075: Web Dashboard Foundation / Dashboard Runtime Integration

Routes return Dashboard View Models.
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

    返回: Dashboard View Models
    """

    @abstractmethod
    def register_routes(self) -> None:
        """注册路由。"""
        ...
