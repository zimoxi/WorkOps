"""
WorkOps OMV Exceptions — OMV 异常
Sprint069: Real OMV API Client
"""


class OMVConnectionError(Exception):
    """OMV 连接错误基类"""
    pass


class OMVAuthenticationError(OMVConnectionError):
    """OMV 认证错误"""
    pass


class OMVReadonlyViolationError(OMVConnectionError):
    """OMV 只读违规"""
    pass


class OMVTimeoutError(OMVConnectionError):
    """OMV 超时"""
    pass
