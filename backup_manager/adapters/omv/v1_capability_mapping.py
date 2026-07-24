"""
WorkOps OMV Capability Mapping — OMV 能力映射
Sprint050: OMV Adapter v1 Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .v1_capability import OMVCapability
from ...devices.capability import DeviceCapability
from .v1_errors import InvalidOMVAdapterError


@dataclass(frozen=True, slots=True)
class OMVCapabilityMapping:
    """
    OMV 能力到设备能力的映射。不可变。
    """

    omv_capability: OMVCapability
    device_capability: DeviceCapability

    def __post_init__(self):
        if not isinstance(self.omv_capability, OMVCapability):
            raise InvalidOMVAdapterError("omv_capability must be an OMVCapability instance")
        if not isinstance(self.device_capability, DeviceCapability):
            raise InvalidOMVAdapterError("device_capability must be a DeviceCapability instance")
