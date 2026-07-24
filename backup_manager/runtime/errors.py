"""
WorkOps Runtime Errors — 运行时错误
Sprint052: ReadOnly Runtime Connector Foundation
"""


class RuntimeError(Exception):
    """运行时错误基类"""
    pass


class InvalidRuntimeRequestError(RuntimeError):
    """无效运行时请求"""
    pass


class RuntimeExecutionError(RuntimeError):
    """运行时执行错误"""
    pass


class RuntimeUnavailableError(RuntimeError):
    """运行时不可用"""
    pass
