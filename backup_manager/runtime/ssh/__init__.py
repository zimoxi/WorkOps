"""
WorkOps SSH Runtime Domain — SSH 运行时域
Sprint058/Sprint067: Linux SSH Runtime Foundation / Real Linux SSH Connector
"""

from .errors import (
    SSHRuntimeError,
    InvalidSSHSessionError,
    SSHExecutionRejectedError,
    SSHConnectionUnavailableError,
)
from .model import SSHSessionMode, SSHSession
from .session import SSHExecutionRequest, validate_ssh_request
from .result import SSHRuntimeResult
from .connector import LinuxSSHConnector, RealLinuxSSHConnector
from .connection import SSHConnectionConfig, SSHConnectionState
from .client import SSHClient
from .readonly import ReadOnlySSHExecutor, validate_readonly_operation, ALLOWED_READONLY_OPERATIONS
from .exceptions import (
    SSHConnectionError,
    SSHAuthenticationError,
    SSHReadonlyViolationError,
    SSHTimeoutError,
)

__all__ = [
    # Sprint058
    "SSHRuntimeError",
    "InvalidSSHSessionError",
    "SSHExecutionRejectedError",
    "SSHConnectionUnavailableError",
    "SSHSessionMode",
    "SSHSession",
    "SSHExecutionRequest",
    "SSHRuntimeResult",
    "LinuxSSHConnector",
    "validate_ssh_request",
    # Sprint067
    "SSHConnectionConfig",
    "SSHConnectionState",
    "SSHClient",
    "ReadOnlySSHExecutor",
    "RealLinuxSSHConnector",
    "validate_readonly_operation",
    "ALLOWED_READONLY_OPERATIONS",
    "SSHConnectionError",
    "SSHAuthenticationError",
    "SSHReadonlyViolationError",
    "SSHTimeoutError",
]
