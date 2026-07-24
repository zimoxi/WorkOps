"""
WorkOps Execution Context Errors — 执行上下文错误
Sprint051: Adapter Execution Context Foundation
"""


class ExecutionContextError(Exception):
    """执行上下文错误基类"""
    pass


class InvalidExecutionContextError(ExecutionContextError):
    """无效执行上下文"""
    pass


class ExecutionContextConflictError(ExecutionContextError):
    """执行上下文冲突"""
    pass
