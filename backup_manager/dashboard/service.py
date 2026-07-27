"""
WorkOps Dashboard Service Contract — 仪表盘服务接口
Sprint073: Web Dashboard Foundation

只定义接口。不实现 HTML 渲染。
"""

from abc import ABC, abstractmethod


class DashboardService(ABC):
    """
    仪表盘服务接口。

    只定义接口。不实现 HTML 渲染。不实现前端逻辑。
    """

    @abstractmethod
    def get_overview(self):
        """获取系统概览。"""
        ...

    @abstractmethod
    def get_runtime_status(self):
        """获取运行时状态。"""
        ...

    @abstractmethod
    def get_backup_status(self):
        """获取备份状态。"""
        ...

    @abstractmethod
    def get_restore_status(self):
        """获取恢复状态。"""
        ...
