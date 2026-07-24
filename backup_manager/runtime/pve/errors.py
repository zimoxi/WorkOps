"""
WorkOps PVE Runtime Errors — PVE 运行时错误
Sprint059: PVE API Runtime Foundation
"""


class PVERuntimeError(Exception):
    """PVE 运行时错误基类"""
    pass


class InvalidPVERuntimeSessionError(PVERuntimeError):
    """无效 PVE 运行时会话"""
    pass


class PVEExecutionRejectedError(PVERuntimeError):
    """PVE 执行被拒绝"""
    pass


class PVEConnectionUnavailableError(PVERuntimeError):
    """PVE 连接不可用"""
    pass
