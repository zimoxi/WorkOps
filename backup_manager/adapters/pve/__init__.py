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
