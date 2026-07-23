"""
WorkOps Adapter Integration Model — 适配器集成模型
Sprint046: Device Adapter Integration Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from ..devices.capability import DeviceCapability
from ..devices.capability import DeviceType
from .adapter_errors import InvalidAdapterError


@dataclass(frozen=True, slots=True)
class AdapterIntegration:
    """
    适配器集成绑定。不可变。
    """

    adapter_id: str
    device_type: DeviceType
    capabilities: tuple  # tuple[DeviceCapability, ...]

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidAdapterError("adapter_id must be a non-empty string")
        if not isinstance(self.device_type, DeviceType):
            raise InvalidAdapterError("device_type must be a DeviceType instance")
        if not isinstance(self.capabilities, tuple):
            raise InvalidAdapterError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, DeviceCapability):
                raise InvalidAdapterError("All capabilities must be DeviceCapability instances")
