"""
WorkOps Linux Adapter Domain — Linux 适配器域
Sprint048: Linux Adapter v1 Foundation
"""

from .errors import (
    LinuxAdapterError,
    InvalidLinuxAdapterError,
    LinuxCapabilityError,
    LinuxOperationError,
)
from .capability import LinuxCapability, LinuxOperation
from .model import LinuxAdapterDescriptor
from .provider import LinuxAdapterProvider
from .capability_mapping import LinuxCapabilityMapping

__all__ = [
    "LinuxAdapterError",
    "InvalidLinuxAdapterError",
    "LinuxCapabilityError",
    "LinuxOperationError",
    "LinuxCapability",
    "LinuxOperation",
    "LinuxAdapterDescriptor",
    "LinuxAdapterProvider",
    "LinuxCapabilityMapping",
]
