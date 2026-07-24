"""
WorkOps PVE Adapter Package — PVE 适配器
Sprint027: PVE ReadOnly Adapter
"""

from .errors import PVEAdapterError, PVEQueryError, PVEUnsupportedOperationError
from .models import PVENodeInfo, PVEStorageInfo, PVEStatus
from .client import PVEClient

__all__ = [
    "PVEAdapterError",
    "PVEQueryError",
    "PVEUnsupportedOperationError",
    "PVENodeInfo",
    "PVEStorageInfo",
    "PVEStatus",
    "PVEClient",
]

# Sprint049: PVE Adapter v1 Foundation
from .v1_errors import (
    PVEAdapterV1Error,
    InvalidPVEAdapterError,
    PVECapabilityError,
    PVEOperationError,
)
from .v1_capability import PVECapability, PVEOperation
from .v1_model import PVEAdapterDescriptor
from .v1_provider import PVEAdapterProvider
from .v1_capability_mapping import PVECapabilityMapping

__all__ += [
    "PVEAdapterV1Error",
    "InvalidPVEAdapterError",
    "PVECapabilityError",
    "PVEOperationError",
    "PVECapability",
    "PVEOperation",
    "PVEAdapterDescriptor",
    "PVEAdapterProvider",
    "PVECapabilityMapping",
]
