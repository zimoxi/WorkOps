"""
WorkOps PVE Exceptions — PVE 异常
Sprint068: Real PVE API Client
"""


class PVEConnectionError(Exception):
    """PVE 连接错误基类"""
    pass


class PVEAuthenticationError(PVEConnectionError):
    """PVE 认证错误"""
    pass


class PVEReadonlyViolationError(PVEConnectionError):
    """PVE 只读违规"""
    pass


class PVETimeoutError(PVEConnectionError):
    """PVE 超时"""
    pass
