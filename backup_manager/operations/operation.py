"""
WorkOps Operation Types and Status — 操作类型和状态枚举
Sprint038: Operation Orchestration Foundation
"""

from enum import Enum


class OperationType(Enum):
    """操作类型。只允许枚举值。"""

    BACKUP = "backup"
    RESTORE = "restore"
    HEALTH_CHECK = "health_check"
    INVENTORY_SCAN = "inventory_scan"


class OperationStatus(Enum):
    """操作状态。"""

    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
