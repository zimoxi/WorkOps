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
from .pve_adapter import PVEAdapter
from .pve import (
    PVEAdapterError,
    PVEQueryError,
    PVEUnsupportedOperationError,
    PVENodeInfo,
    PVEStorageInfo,
    PVEStatus,
    PVEClient,
)
from .omv_adapter import OMVAdapter
from .omv import (
    OMVAdapterError,
    OMVQueryError,
    OMVUnsupportedOperationError,
    OMVSystemInfo,
    OMVStorageInfo,
    OMVStatus,
    OMVClient,
)

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
    "PVEAdapter",
    "PVEAdapterError",
    "PVEQueryError",
    "PVEUnsupportedOperationError",
    "PVENodeInfo",
    "PVEStorageInfo",
    "PVEStatus",
    "PVEClient",
    "OMVAdapter",
    "OMVAdapterError",
    "OMVQueryError",
    "OMVUnsupportedOperationError",
    "OMVSystemInfo",
    "OMVStorageInfo",
    "OMVStatus",
    "OMVClient",
]

# Sprint046: Adapter Integration Foundation
from .adapter_errors import (
    AdapterIntegrationError,
    InvalidAdapterError,
    AdapterConflictError,
    AdapterNotFoundError as AdapterIntegrationNotFoundError,
)
from .adapter_model import AdapterType
from .adapter_descriptor import AdapterDescriptor
from .adapter_provider import AdapterProvider
from .adapter_registry import AdapterIntegrationRegistry
from .adapter_integration import AdapterIntegration

__all__ += [
    "AdapterIntegrationError",
    "InvalidAdapterError",
    "AdapterConflictError",
    "AdapterIntegrationNotFoundError",
    "AdapterType",
    "AdapterDescriptor",
    "AdapterProvider",
    "AdapterIntegrationRegistry",
    "AdapterIntegration",
]
