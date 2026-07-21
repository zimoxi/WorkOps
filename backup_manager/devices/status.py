"""
WorkOps Device Status — 设备状态枚举
Sprint025: Device Inventory
"""

from enum import Enum


class DeviceStatus(Enum):
    """设备状态。只允许枚举值。"""

    UNKNOWN = "unknown"
    ACTIVE = "active"
    DISABLED = "disabled"
    RETIRED = "retired"
