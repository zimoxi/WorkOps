"""
WorkOps OMV Adapter Package — OMV 适配器
Sprint028: OMV ReadOnly Adapter
"""

from .errors import OMVAdapterError, OMVQueryError, OMVUnsupportedOperationError
from .models import OMVSystemInfo, OMVStorageInfo, OMVStatus
from .client import OMVClient

__all__ = [
    "OMVAdapterError",
    "OMVQueryError",
    "OMVUnsupportedOperationError",
    "OMVSystemInfo",
    "OMVStorageInfo",
    "OMVStatus",
    "OMVClient",
]

# Sprint050: OMV Adapter v1 Foundation
from .v1_errors import (
    OMVAdapterV1Error,
    InvalidOMVAdapterError,
    OMVCapabilityError,
    OMVOperationError,
)
from .v1_capability import OMVCapability, OMVOperation
from .v1_model import OMVAdapterDescriptor
from .v1_provider import OMVAdapterProvider
from .v1_capability_mapping import OMVCapabilityMapping

__all__ += [
    "OMVAdapterV1Error",
    "InvalidOMVAdapterError",
    "OMVCapabilityError",
    "OMVOperationError",
    "OMVCapability",
    "OMVOperation",
    "OMVAdapterDescriptor",
    "OMVAdapterProvider",
    "OMVCapabilityMapping",
]
