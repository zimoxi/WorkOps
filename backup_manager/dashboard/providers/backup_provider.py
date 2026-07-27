"""
WorkOps Backup Dashboard Provider — 备份仪表盘数据提供者
Sprint075: Dashboard Runtime Integration

Returns BackupOverview.
No paths. No credentials. No tokens.
"""

from abc import ABC, abstractmethod

from ..models import BackupOverview


class BackupDashboardProvider(ABC):
    """
    备份仪表盘数据提供者接口。

    返回: BackupOverview

    不暴露: 路径、凭证、令牌
    """

    @abstractmethod
    def get_backup_overview(self) -> BackupOverview:
        """
        获取备份概览。

        Returns:
            BackupOverview
        """
        ...
