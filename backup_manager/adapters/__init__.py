"""
WorkOps Device Adapter Layer
Sprint017: Device Adapter Foundation
Sprint022: 新增 SSH ReadOnly Adapter
Sprint023: 新增 Runtime 层
Sprint026: 新增 Capability Registry
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
    AdapterDescriptorError,
    AdapterDuplicateError,
    AdapterNotRegisteredError,
    AdapterSessionStateError,
    AdapterCapabilityError,
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
    CapabilityNotSupportedError,
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
from .capabilities import AdapterCapability
from .descriptor import AdapterDescriptor
from .registry import AdapterRegistry
from .session import AdapterSession, SessionState
from .runtime import AdapterRuntime
from .result import AdapterQueryResult
from .capability import AdapterCapabilityDeclaration
from .capability_registry import AdapterCapabilityRegistry
from .contracts import AdapterCapabilityProvider

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
    "AdapterDescriptorError",
    "AdapterDuplicateError",
    "AdapterNotRegisteredError",
    "AdapterSessionStateError",
    "AdapterCapabilityError",
    "AdapterAlreadyExistsError",
    "AdapterNotFoundError",
    "CapabilityNotSupportedError",
    "SSHAdapterError",
    "SSHConfigurationError",
    "SSHAuthenticationError",
    "SSHHostKeyError",
    "SSHConnectionError",
    "SSHTimeoutError",
    "SSHQueryNotAllowedError",
    "SSHQueryExecutionError",
    "SSHReadOnlyAdapter",
    "AdapterCapability",
    "AdapterDescriptor",
    "AdapterRegistry",
    "AdapterSession",
    "SessionState",
    "AdapterRuntime",
    "AdapterQueryResult",
    "AdapterCapabilityDeclaration",
    "AdapterCapabilityRegistry",
    "AdapterCapabilityProvider",
]
