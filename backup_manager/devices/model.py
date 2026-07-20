"""
WorkOps Device Model — 设备域模型
Sprint024: Device Capability Model

frozen dataclass。不包含任何 secret/credential 信息。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .capability import DeviceCapability, DeviceType
from .errors import DeviceModelValidationError


@dataclass(frozen=True, slots=True)
class DeviceModel:
    """
    设备模型。不可变。

    只描述设备能力，不包含任何连接/认证信息。
    """

    device_id: str
    name: str
    device_type: DeviceType
    capabilities: tuple  # tuple[DeviceCapability, ...]
    enabled: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        # device_id 校验
        if not isinstance(self.device_id, str) or not self.device_id.strip():
            raise DeviceModelValidationError("device_id must be a non-empty string")

        # name 校验
        if not isinstance(self.name, str) or not self.name.strip():
            raise DeviceModelValidationError("name must be a non-empty string")

        # device_type 校验
        if not isinstance(self.device_type, DeviceType):
            raise DeviceModelValidationError("device_type must be a DeviceType instance")

        # capabilities 校验 — 必须是 tuple
        if not isinstance(self.capabilities, tuple):
            raise DeviceModelValidationError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, DeviceCapability):
                raise DeviceModelValidationError(
                    "All capabilities must be DeviceCapability instances"
                )

        # enabled 校验
        if not isinstance(self.enabled, bool):
            raise DeviceModelValidationError("enabled must be a bool")
