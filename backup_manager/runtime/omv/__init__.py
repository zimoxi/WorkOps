"""
WorkOps OMV Runtime Domain — OMV 运行时域
Sprint060/Sprint069: OMV API Runtime Foundation / Real OMV API Client
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
from .connector import OMVAPIConnector, RealOMVAPIConnector
from .connection import OMVConnectionConfig, OMVRuntimeState
from .client import OMVAPIClient
from .readonly import OMVReadOnlyExecutor, validate_omv_readonly_operation, ALLOWED_READONLY_OPERATIONS
from .exceptions import (
    OMVConnectionError,
    OMVAuthenticationError,
    OMVReadonlyViolationError,
    OMVTimeoutError,
)

__all__ = [
    # Sprint060
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
    # Sprint069
    "OMVConnectionConfig",
    "OMVRuntimeState",
    "OMVAPIClient",
    "OMVReadOnlyExecutor",
    "RealOMVAPIConnector",
    "validate_omv_readonly_operation",
    "ALLOWED_READONLY_OPERATIONS",
    "OMVConnectionError",
    "OMVAuthenticationError",
    "OMVReadonlyViolationError",
    "OMVTimeoutError",
]
