"""
WorkOps Restore Dashboard Provider — 恢复仪表盘数据提供者
Sprint075: Dashboard Runtime Integration

Returns RestoreOverview.
"""

from abc import ABC, abstractmethod

from ..models import RestoreOverview


class RestoreDashboardProvider(ABC):
    """
    恢复仪表盘数据提供者接口。

    返回: RestoreOverview
    """

    @abstractmethod
    def get_restore_overview(self) -> RestoreOverview:
        """
        获取恢复概览。

        Returns:
            RestoreOverview
        """
        ...
