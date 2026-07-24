"""
WorkOps OMV Runtime Errors — OMV 运行时错误
Sprint060: OMV API Runtime Foundation
"""


class OMVRuntimeError(Exception):
    """OMV 运行时错误基类"""
    pass


class InvalidOMVRuntimeSessionError(OMVRuntimeError):
    """无效 OMV 运行时会话"""
    pass


class OMVExecutionRejectedError(OMVRuntimeError):
    """OMV 执行被拒绝"""
    pass


class OMVConnectionUnavailableError(OMVRuntimeError):
    """OMV 连接不可用"""
    pass
