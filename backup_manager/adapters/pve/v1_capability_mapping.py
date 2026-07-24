"""
WorkOps PVE Capability Mapping — PVE 能力映射
Sprint049: PVE Adapter v1 Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .v1_capability import PVECapability
from ...devices.capability import DeviceCapability
from .v1_errors import InvalidPVEAdapterError


@dataclass(frozen=True, slots=True)
class PVECapabilityMapping:
    """
    PVE 能力到设备能力的映射。不可变。
    """

    pve_capability: PVECapability
    device_capability: DeviceCapability

    def __post_init__(self):
        if not isinstance(self.pve_capability, PVECapability):
            raise InvalidPVEAdapterError("pve_capability must be a PVECapability instance")
        if not isinstance(self.device_capability, DeviceCapability):
            raise InvalidPVEAdapterError("device_capability must be a DeviceCapability instance")
