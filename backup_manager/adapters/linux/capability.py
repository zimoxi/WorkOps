"""
WorkOps Linux Capability — Linux 能力枚举
Sprint048: Linux Adapter v1 Foundation
"""

from enum import Enum


class LinuxCapability(Enum):
    """Linux 能力。"""

    SYSTEM_INFO = "system_info"
    STORAGE_INFO = "storage_info"
    NETWORK_INFO = "network_info"
    SERVICE_STATUS = "service_status"


class LinuxOperation(Enum):
    """Linux 操作。"""

    QUERY_SYSTEM = "query_system"
    QUERY_STORAGE = "query_storage"
    QUERY_NETWORK = "query_network"
    QUERY_SERVICE = "query_service"
