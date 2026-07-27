"""
WorkOps Dashboard Service — 仪表盘服务
Sprint073/Sprint075: Web Dashboard Foundation / Dashboard Runtime Integration

Aggregates providers. No direct runtime access.
"""

from abc import ABC, abstractmethod

from .models import (
    DashboardViewModel,
    DashboardStatus,
    RuntimeOverview,
    BackupOverview,
    RestoreOverview,
)
from .providers.health_provider import HealthSummary
from .providers.metrics_provider import MetricsSummary
from .providers.audit_provider import AuditSummary


class DashboardService(ABC):
    """
    仪表盘服务接口。

    聚合数据提供者。不直接访问运行时。
    """

    @abstractmethod
    def get_overview(self) -> DashboardViewModel:
        """获取系统概览。"""
        ...

    @abstractmethod
    def get_runtime_status(self) -> list:
        """获取运行时状态。 Returns list[RuntimeOverview]"""
        ...

    @abstractmethod
    def get_backup_status(self) -> BackupOverview:
        """获取备份状态。"""
        ...

    @abstractmethod
    def get_restore_status(self) -> RestoreOverview:
        """获取恢复状态。"""
        ...

    @abstractmethod
    def get_health_status(self) -> HealthSummary:
        """获取健康状态。"""
        ...

    @abstractmethod
    def get_metrics_status(self) -> MetricsSummary:
        """获取指标状态。"""
        ...

    @abstractmethod
    def get_audit_status(self) -> AuditSummary:
        """获取审计状态。"""
        ...
