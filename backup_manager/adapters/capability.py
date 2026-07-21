"""
WorkOps Adapter Capability Declaration — 能力声明
Sprint026: Adapter Capability Registry

冻结数据模型。描述 Adapter 提供的能力。
"""

from dataclasses import dataclass

from ..devices.capability import DeviceCapability
from .errors import AdapterCapabilityError


@dataclass(frozen=True, slots=True)
class AdapterCapabilityDeclaration:
    """
    Adapter 能力声明。不可变。

    描述某个 adapter_type 提供哪些 DeviceCapability。
    """

    adapter_type: str
    capabilities: tuple  # tuple[DeviceCapability, ...]

    def __post_init__(self):
        if not isinstance(self.adapter_type, str) or not self.adapter_type.strip():
            raise AdapterCapabilityError("adapter_type must be a non-empty string")
        if not isinstance(self.capabilities, tuple):
            raise AdapterCapabilityError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, DeviceCapability):
                raise AdapterCapabilityError(
                    "All capabilities must be DeviceCapability instances"
                )
