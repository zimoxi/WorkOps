"""
WorkOps Runtime Mode — 运行时模式枚举
Sprint052: ReadOnly Runtime Connector Foundation
"""

from enum import Enum


class RuntimeMode(Enum):
    """运行时模式。"""

    READ_ONLY = "read_only"
    MUTATION = "mutation"
