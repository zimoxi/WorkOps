"""
WorkOps Device Capability — 设备类型和能力枚举
Sprint024: Device Capability Model

不可变枚举。不允许任意字符串。
"""

from enum import Enum


class DeviceType(Enum):
    """设备类型。只允许枚举值。"""

    UNKNOWN = "unknown"
    SERVER = "server"
    NAS = "nas"
    VIRTUALIZATION_HOST = "virtualization_host"
    ROUTER = "router"


class DeviceCapability(Enum):
    """设备能力。不可变。不允许动态注册。"""

    STATUS_QUERY = "status_query"
    SYSTEM_INFO = "system_info"
    STORAGE_QUERY = "storage_query"
    NETWORK_QUERY = "network_query"
    BACKUP_SOURCE = "backup_source"
    BACKUP_TARGET = "backup_target"
