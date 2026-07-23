"""
WorkOps Linux Adapter Descriptor — Linux 适配器描述符
Sprint048: Linux Adapter v1 Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .capability import LinuxCapability
from .errors import InvalidLinuxAdapterError


@dataclass(frozen=True, slots=True)
class LinuxAdapterDescriptor:
    """
    Linux 适配器描述符。不可变。
    """

    adapter_id: str
    version: str
    capabilities: tuple  # tuple[LinuxCapability, ...]

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidLinuxAdapterError("adapter_id must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise InvalidLinuxAdapterError("version must be a non-empty string")
        if not isinstance(self.capabilities, tuple):
            raise InvalidLinuxAdapterError("capabilities must be a tuple")
        for cap in self.capabilities:
            if not isinstance(cap, LinuxCapability):
                raise InvalidLinuxAdapterError("All capabilities must be LinuxCapability instances")
