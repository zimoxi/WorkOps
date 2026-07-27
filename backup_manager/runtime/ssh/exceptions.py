"""
WorkOps SSH Exceptions — SSH 异常
Sprint067: Real Linux SSH Connector
"""


class SSHConnectionError(Exception):
    """SSH 连接错误基类"""
    pass


class SSHAuthenticationError(SSHConnectionError):
    """SSH 认证错误"""
    pass


class SSHReadonlyViolationError(SSHConnectionError):
    """SSH 只读违规"""
    pass


class SSHTimeoutError(SSHConnectionError):
    """SSH 超时"""
    pass
