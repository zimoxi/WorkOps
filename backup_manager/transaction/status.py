"""
WorkOps Transaction Status — 事务状态枚举
Sprint056: Operation Transaction System Foundation
"""

from enum import Enum


class TransactionStatus(Enum):
    """事务状态。"""

    CREATED = "created"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
