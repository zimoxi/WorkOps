"""
WorkOps Device Domain — 设备域
Sprint024: Device Capability Model
Sprint025: Device Inventory
"""

from .capability import DeviceType, DeviceCapability
from .model import DeviceModel
from .status import DeviceStatus
from .inventory import DeviceRecord
from .matcher import CapabilityRequirement, CapabilityMatcher
from .registry import DeviceCapabilityRegistry
from .repository import DeviceInventoryRepository
from .service import DeviceInventoryService
from .errors import (
    DeviceError,
    DeviceTypeError,
    DeviceCapabilityError,
    DeviceModelValidationError,
    CapabilityRequirementError,
    InvalidDeviceError,
    CapabilityNotFoundError,
    CapabilityConflictError,
    DeviceInventoryError,
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)

__all__ = [
    "DeviceType",
    "DeviceCapability",
    "DeviceModel",
    "DeviceStatus",
    "DeviceRecord",
    "CapabilityRequirement",
    "CapabilityMatcher",
    "DeviceCapabilityRegistry",
    "DeviceInventoryRepository",
    "DeviceInventoryService",
    "DeviceError",
    "DeviceTypeError",
    "DeviceCapabilityError",
    "DeviceModelValidationError",
    "CapabilityRequirementError",
    "InvalidDeviceError",
    "CapabilityNotFoundError",
    "CapabilityConflictError",
    "DeviceInventoryError",
    "DeviceAlreadyExistsError",
    "DeviceNotFoundError",
]
