"""
WorkOps Device Domain — 设备域
Sprint024: Device Capability Model
"""

from .capability import DeviceType, DeviceCapability
from .model import DeviceModel
from .matcher import CapabilityRequirement, CapabilityMatcher
from .registry import DeviceCapabilityRegistry
from .errors import (
    DeviceError,
    DeviceTypeError,
    DeviceCapabilityError,
    DeviceModelValidationError,
    CapabilityRequirementError,
    InvalidDeviceError,
    CapabilityNotFoundError,
    CapabilityConflictError,
)

__all__ = [
    "DeviceType",
    "DeviceCapability",
    "DeviceModel",
    "CapabilityRequirement",
    "CapabilityMatcher",
    "DeviceCapabilityRegistry",
    "DeviceError",
    "DeviceTypeError",
    "DeviceCapabilityError",
    "DeviceModelValidationError",
    "CapabilityRequirementError",
    "InvalidDeviceError",
    "CapabilityNotFoundError",
    "CapabilityConflictError",
]
