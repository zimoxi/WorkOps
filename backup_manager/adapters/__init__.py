"""
WorkOps Device Adapter Layer
Sprint017: Device Adapter Foundation
Sprint022: 新增 SSH ReadOnly Adapter
"""

from .base import BaseAdapter
from .mock_adapter import MockAdapter
from .ssh_adapter import SSHAdapter
from .winrm_adapter import WinRMAdapter
from .snmp_adapter import SNMPAdapter
from .factory import AdapterFactory
from .errors import (
    AdapterError,
    AdapterNotConnectedError,
    AdapterNotImplementedError,
    AdapterExecutionError,
)
from .ssh_errors import (
    SSHAdapterError,
    SSHConfigurationError,
    SSHAuthenticationError,
    SSHHostKeyError,
    SSHConnectionError,
    SSHTimeoutError,
    SSHQueryNotAllowedError,
    SSHQueryExecutionError,
)
from .ssh_readonly_adapter import SSHReadOnlyAdapter

__all__ = [
    "BaseAdapter",
    "MockAdapter",
    "SSHAdapter",
    "WinRMAdapter",
    "SNMPAdapter",
    "AdapterFactory",
    "AdapterError",
    "AdapterNotConnectedError",
    "AdapterNotImplementedError",
    "AdapterExecutionError",
    "SSHAdapterError",
    "SSHConfigurationError",
    "SSHAuthenticationError",
    "SSHHostKeyError",
    "SSHConnectionError",
    "SSHTimeoutError",
    "SSHQueryNotAllowedError",
    "SSHQueryExecutionError",
    "SSHReadOnlyAdapter",
]
