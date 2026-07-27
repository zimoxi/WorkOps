"""
WorkOps Runtime Health Models — 运行时健康模型
Sprint076: Runtime Health Probe and Device Inventory

RuntimeHealthStatus, RuntimeDevice, RuntimeHealthResult
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidRuntimeDeviceError


class RuntimeHealthStatus(Enum):
    """运行时健康状态。"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class RuntimeDevice:
    """
    运行时设备。不可变。
    """

    device_id: str
    device_type: str
    display_name: str
    status: RuntimeHealthStatus
    checked_at: datetime = None

    def __post_init__(self):
        for field_name in ["device_id", "device_type", "display_name"]:
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise InvalidRuntimeDeviceError(f"{field_name} must be a non-empty string")
        if not isinstance(self.status, RuntimeHealthStatus):
            raise InvalidRuntimeDeviceError("status must be a RuntimeHealthStatus instance")
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class RuntimeHealthResult:
    """
    运行时健康检查结果。不可变。
    """

    device_id: str
    status: RuntimeHealthStatus
    message: str
    checked_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise InvalidRuntimeDeviceError("device_id must be a non-empty string")
        if not isinstance(self.status, RuntimeHealthStatus):
            raise InvalidRuntimeDeviceError("status must be a RuntimeHealthStatus instance")
        if not isinstance(self.message, str):
            raise InvalidRuntimeDeviceError("message must be a string")
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", datetime.now(timezone.utc))
