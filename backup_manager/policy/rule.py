"""
WorkOps Policy Rules — 策略效果和类型枚举
Sprint044: Policy Engine Foundation
"""

from enum import Enum


class PolicyEffect(Enum):
    """策略效果。"""

    ALLOW = "allow"
    DENY = "deny"


class PolicyType(Enum):
    """策略类型。"""

    OPERATION = "operation"
    DEVICE = "device"
    HEALTH = "health"
