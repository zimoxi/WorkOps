"""
WorkOps Device Models — 设备模型
Sprint077: Device Management Foundation

DeviceType, DeviceStatus, Device
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidDeviceError


class DeviceType(Enum):
    """设备类型。"""

    LINUX = "linux"
    PVE = "pve"
    OMV = "omv"


class DeviceStatus(Enum):
    """设备状态。"""

    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Device:
    """
    设备。不可变。
    """

    device_id: str
    device_type: DeviceType
    display_name: str
    status: DeviceStatus
    created_at: datetime
    last_seen_at: datetime

    def __post_init__(self):
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidDeviceError("device_id must be a non-empty string")
        if not isinstance(self.device_type, DeviceType):
            raise InvalidDeviceError("device_type must be a DeviceType instance")
        if not isinstance(self.display_name, str) or not self.display_name.strip():
            raise InvalidDeviceError("display_name must be a non-empty string")
        if not isinstance(self.status, DeviceStatus):
            raise InvalidDeviceError("status must be a DeviceStatus instance")
        if not isinstance(self.created_at, datetime):
            raise InvalidDeviceError("created_at must be a datetime instance")
        if not isinstance(self.last_seen_at, datetime):
            raise InvalidDeviceError("last_seen_at must be a datetime instance")
