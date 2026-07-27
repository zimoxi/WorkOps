"""
WorkOps Dashboard Domain — 仪表盘域
Sprint073/Sprint075: Web Dashboard Foundation / Dashboard Runtime Integration
"""

from .errors import (
    DashboardError,
    DashboardUnavailableError,
    InvalidDashboardRequestError,
)
from .models import (
    DashboardStatus,
    DashboardViewModel,
    RuntimeOverview,
    BackupOverview,
    RestoreOverview,
)
from .service import DashboardService
from .routes import DashboardRoutes
from .providers import (
    RuntimeDashboardProvider,
    BackupDashboardProvider,
    RestoreDashboardProvider,
    HealthDashboardProvider,
    MetricsDashboardProvider,
    AuditDashboardProvider,
)
from .providers.health_provider import HealthSummary
from .providers.metrics_provider import MetricsSummary
from .providers.audit_provider import AuditSummary

__all__ = [
    "DashboardError",
    "DashboardUnavailableError",
    "InvalidDashboardRequestError",
    "DashboardStatus",
    "DashboardViewModel",
    "RuntimeOverview",
    "BackupOverview",
    "RestoreOverview",
    "DashboardService",
    "DashboardRoutes",
    "RuntimeDashboardProvider",
    "BackupDashboardProvider",
    "RestoreDashboardProvider",
    "HealthDashboardProvider",
    "MetricsDashboardProvider",
    "AuditDashboardProvider",
    "HealthSummary",
    "MetricsSummary",
    "AuditSummary",
]
