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
