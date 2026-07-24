"""
WorkOps PVE Adapter Descriptor — PVE 适配器描述符
Sprint049: PVE Adapter v1 Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .v1_capability import PVECapability
from .v1_errors import InvalidPVEAdapterError


@dataclass(frozen=True, slots=True)
class PVEAdapterDescriptor:
    """
    PVE 适配器描述符。不可变。
    """

    adapter_id: str
    version: str
    capabilities: tuple  # tuple[PVECapability, ...]

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidPVEAdapterError("adapter_id must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise InvalidPVEAdapterError("version must be a non-empty string")
        if not isinstance(self.capabilities, tuple):
            raise InvalidPVEAdapterError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, PVECapability):
                raise InvalidPVEAdapterError("All capabilities must be PVECapability instances")
