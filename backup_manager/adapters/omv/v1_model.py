"""
WorkOps OMV Adapter Descriptor — OMV 适配器描述符
Sprint050: OMV Adapter v1 Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .v1_capability import OMVCapability
from .v1_errors import InvalidOMVAdapterError


@dataclass(frozen=True, slots=True)
class OMVAdapterDescriptor:
    """
    OMV 适配器描述符。不可变。
    """

    adapter_id: str
    version: str
    capabilities: tuple  # tuple[OMVCapability, ...]

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidOMVAdapterError("adapter_id must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise InvalidOMVAdapterError("version must be a non-empty string")
        if not isinstance(self.capabilities, tuple):
            raise InvalidOMVAdapterError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, OMVCapability):
                raise InvalidOMVAdapterError("All capabilities must be OMVCapability instances")
