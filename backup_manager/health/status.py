"""
WorkOps Health Status — 健康状态和检查类型枚举
Sprint043: Device Health Monitoring Foundation
"""

from enum import Enum


class HealthStatus(Enum):
    """健康状态。"""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    OFFLINE = "offline"


class HealthCheckType(Enum):
    """健康检查类型。"""

    SYSTEM = "system"
    STORAGE = "storage"
    NETWORK = "network"
    SERVICE = "service"
