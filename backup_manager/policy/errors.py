"""
WorkOps Policy Errors — 策略引擎错误
Sprint044: Policy Engine Foundation
"""


class PolicyError(Exception):
    """策略错误基类"""
    pass


class InvalidPolicyError(PolicyError):
    """无效策略"""
    pass


class PolicyConflictError(PolicyError):
    """策略冲突"""
    def __init__(self, policy_id: str):
        super().__init__(f"Policy already exists: {policy_id}")


class PolicyNotFoundError(PolicyError):
    """策略未找到"""
    def __init__(self, policy_id: str):
        super().__init__(f"Policy not found: {policy_id}")
