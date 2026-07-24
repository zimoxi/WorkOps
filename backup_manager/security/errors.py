"""
WorkOps Security Errors — 安全错误
Sprint057: Runtime Security Hardening Foundation
"""


class SecurityError(Exception):
    """安全错误基类"""
    pass


class InvalidSecurityContextError(SecurityError):
    """无效安全上下文"""
    pass


class SecurityViolationError(SecurityError):
    """安全违规"""
    pass


class SecurityPolicyError(SecurityError):
    """安全策略错误"""
    pass
