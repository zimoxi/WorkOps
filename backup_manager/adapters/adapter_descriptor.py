"""
WorkOps Adapter Descriptor — 适配器描述符
Sprint046: Device Adapter Integration Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .adapter_model import AdapterType
from .adapter_errors import InvalidAdapterError
from ..devices.capability import DeviceCapability


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    """
    适配器描述符。不可变。
    """

    adapter_id: str
    adapter_type: AdapterType
    capabilities: tuple  # tuple[DeviceCapability, ...]
    version: str

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidAdapterError("adapter_id must be a non-empty string")
        if not isinstance(self.adapter_type, AdapterType):
            raise InvalidAdapterError("adapter_type must be an AdapterType instance")
        if not isinstance(self.capabilities, tuple):
            raise InvalidAdapterError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, DeviceCapability):
                raise InvalidAdapterError("All capabilities must be DeviceCapability instances")
        if not isinstance(self.version, str) or not self.version.strip():
            raise InvalidAdapterError("version must be a non-empty string")
