"""
WorkOps Device Record — 设备记录
Sprint025: Device Inventory

frozen dataclass。不包含任何连接/认证信息。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .capability import DeviceCapability, DeviceType
from .status import DeviceStatus
from .errors import DeviceInventoryError


@dataclass(frozen=True, slots=True)
class DeviceRecord:
    """
    设备记录。不可变。

    只描述设备元数据，不包含任何连接/认证信息。
    """

    device_id: str
    name: str
    device_type: DeviceType
    capabilities: tuple  # tuple[DeviceCapability, ...]
    adapter_type: str
    status: DeviceStatus = DeviceStatus.UNKNOWN
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise DeviceInventoryError("device_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise DeviceInventoryError("name must be a non-empty string")
        if not isinstance(self.device_type, DeviceType):
            raise DeviceInventoryError("device_type must be a DeviceType instance")
        if not isinstance(self.capabilities, tuple):
            raise DeviceInventoryError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, DeviceCapability):
                raise DeviceInventoryError(
                    "All capabilities must be DeviceCapability instances"
                )
        if not isinstance(self.adapter_type, str) or not self.adapter_type.strip():
            raise DeviceInventoryError("adapter_type must be a non-empty string")
        if not isinstance(self.status, DeviceStatus):
            raise DeviceInventoryError("status must be a DeviceStatus instance")
