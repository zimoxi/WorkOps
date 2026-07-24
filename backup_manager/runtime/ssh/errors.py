"""
WorkOps SSH Runtime Errors — SSH 运行时错误
Sprint058: Linux SSH Runtime Foundation
"""


class SSHRuntimeError(Exception):
    """SSH 运行时错误基类"""
    pass


class InvalidSSHSessionError(SSHRuntimeError):
    """无效 SSH 会话"""
    pass


class SSHExecutionRejectedError(SSHRuntimeError):
    """SSH 执行被拒绝"""
    pass


class SSHConnectionUnavailableError(SSHRuntimeError):
    """SSH 连接不可用"""
    pass
