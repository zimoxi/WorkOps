"""
WorkOps Restore Execution State — 恢复执行状态
Sprint036: Restore Workflow Foundation
"""

from enum import Enum


class RestoreExecutionState(Enum):
    """恢复执行状态枚举。"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
