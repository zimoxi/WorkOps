"""
WorkOps Device Adapter Layer
Sprint017: Device Adapter Foundation

建立 Device Adapter 抽象层
独立于 TaskService，未来 Sprint018 才接入
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
]
