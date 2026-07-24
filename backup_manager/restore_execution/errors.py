"""
WorkOps Restore Execution Errors — 恢复执行错误
Sprint054: Restore Execution Pipeline Foundation
"""


class RestoreExecutionError(Exception):
    """恢复执行错误基类"""
    pass


class InvalidRestoreExecutionRequestError(RestoreExecutionError):
    """无效恢复执行请求"""
    pass


class RestoreExecutionConflictError(RestoreExecutionError):
    """恢复执行冲突"""
    def __init__(self, restore_id: str):
        super().__init__(f"Restore execution already exists: {restore_id}")


class RestoreExecutionUnavailableError(RestoreExecutionError):
    """恢复执行不可用"""
    pass
