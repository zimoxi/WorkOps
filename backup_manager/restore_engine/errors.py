"""
WorkOps Restore Engine Errors — 恢复引擎错误
Sprint071: Real Restore Execution Engine
"""


class RestoreEngineError(Exception):
    """恢复引擎错误基类"""
    pass


class InvalidRestoreExecutionError(RestoreEngineError):
    """无效恢复执行"""
    pass


class RestoreRuntimeUnavailableError(RestoreEngineError):
    """恢复运行时不可用"""
    pass


class RestoreExecutionTimeoutError(RestoreEngineError):
    """恢复执行超时"""
    pass
