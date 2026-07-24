"""
WorkOps OMV Capability — OMV 能力枚举
Sprint050: OMV Adapter v1 Foundation
"""

from enum import Enum


class OMVCapability(Enum):
    """OMV 能力。"""

    SYSTEM_INFO = "system_info"
    STORAGE_INFO = "storage_info"
    SHARE_INFO = "share_info"
    BACKUP_CAPABILITY = "backup_capability"


class OMVOperation(Enum):
    """OMV 操作。"""

    QUERY_SYSTEM = "query_system"
    QUERY_STORAGE = "query_storage"
    QUERY_SHARE = "query_share"
    QUERY_BACKUP = "query_backup"
