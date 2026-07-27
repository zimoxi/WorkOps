"""
WorkOps PVE Runtime Domain — PVE 运行时域
Sprint059/Sprint068: PVE API Runtime Foundation / Real PVE API Client
"""

from .errors import (
    PVERuntimeError,
    InvalidPVERuntimeSessionError,
    PVEExecutionRejectedError,
    PVEConnectionUnavailableError,
)
from .model import PVERuntimeMode, PVERuntimeSession
from .request import PVEAPIRequest, validate_pve_request
from .result import PVERuntimeResult
from .connector import PVEAPIConnector, RealPVEAPIConnector
from .connection import PVEConnectionConfig, PVERuntimeState
from .client import PVEAPIClient
from .readonly import PVEReadOnlyExecutor, validate_pve_readonly_operation, ALLOWED_READONLY_OPERATIONS
from .exceptions import (
    PVEConnectionError,
    PVEAuthenticationError,
    PVEReadonlyViolationError,
    PVETimeoutError,
)

__all__ = [
    # Sprint059
    "PVERuntimeError",
    "InvalidPVERuntimeSessionError",
    "PVEExecutionRejectedError",
    "PVEConnectionUnavailableError",
    "PVERuntimeMode",
    "PVERuntimeSession",
    "PVEAPIRequest",
    "PVERuntimeResult",
    "PVEAPIConnector",
    "validate_pve_request",
    # Sprint068
    "PVEConnectionConfig",
    "PVERuntimeState",
    "PVEAPIClient",
    "PVEReadOnlyExecutor",
    "RealPVEAPIConnector",
    "validate_pve_readonly_operation",
    "ALLOWED_READONLY_OPERATIONS",
    "PVEConnectionError",
    "PVEAuthenticationError",
    "PVEReadonlyViolationError",
    "PVETimeoutError",
]
