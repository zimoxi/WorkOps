"""
WorkOps Linux Capability Mapping — Linux 能力映射
Sprint048: Linux Adapter v1 Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .capability import LinuxCapability
from ...devices.capability import DeviceCapability
from .errors import InvalidLinuxAdapterError


@dataclass(frozen=True, slots=True)
class LinuxCapabilityMapping:
    """
    Linux 能力到设备能力的映射。不可变。
    """

    linux_capability: LinuxCapability
    device_capability: DeviceCapability

    def __post_init__(self):
        if not isinstance(self.linux_capability, LinuxCapability):
            raise InvalidLinuxAdapterError("linux_capability must be a LinuxCapability instance")
        if not isinstance(self.device_capability, DeviceCapability):
            raise InvalidLinuxAdapterError("device_capability must be a DeviceCapability instance")
