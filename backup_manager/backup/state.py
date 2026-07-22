"""
WorkOps Backup Execution State — 备份执行状态
Sprint029: Backup Workflow Foundation
"""

from enum import Enum


class BackupExecutionState(Enum):
    """备份执行状态枚举。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
