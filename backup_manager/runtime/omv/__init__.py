"""
WorkOps OMV Runtime Domain — OMV 运行时域
Sprint060: OMV API Runtime Foundation
"""

from .errors import (
    OMVRuntimeError,
    InvalidOMVRuntimeSessionError,
    OMVExecutionRejectedError,
    OMVConnectionUnavailableError,
)
from .model import OMVRuntimeMode, OMVRuntimeSession
from .request import OMVAPIRequest, validate_omv_request
from .result import OMVRuntimeResult
from .connector import OMVAPIConnector

__all__ = [
    "OMVRuntimeError",
    "InvalidOMVRuntimeSessionError",
    "OMVExecutionRejectedError",
    "OMVConnectionUnavailableError",
    "OMVRuntimeMode",
    "OMVRuntimeSession",
    "OMVAPIRequest",
    "OMVRuntimeResult",
    "OMVAPIConnector",
    "validate_omv_request",
]
