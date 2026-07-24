"""
WorkOps PVE Capability — PVE 能力枚举
Sprint049: PVE Adapter v1 Foundation
"""

from enum import Enum


class PVECapability(Enum):
    """PVE 能力。"""

    NODE_INFO = "node_info"
    VM_INFO = "vm_info"
    STORAGE_INFO = "storage_info"
    BACKUP_CAPABILITY = "backup_capability"


class PVEOperation(Enum):
    """PVE 操作。"""

    QUERY_NODE = "query_node"
    QUERY_VM = "query_vm"
    QUERY_STORAGE = "query_storage"
    QUERY_BACKUP = "query_backup"
