"""
WorkOps Execution Mode — 执行模式枚举
Sprint051: Adapter Execution Context Foundation
"""

from enum import Enum


class ExecutionMode(Enum):
    """执行模式。"""

    READ_ONLY = "read_only"
    MUTATION = "mutation"
