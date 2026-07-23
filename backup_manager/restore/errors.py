"""
WorkOps Restore Errors — 恢复工作流错误
Sprint036: Restore Workflow Foundation
Sprint037: Restore Execution Framework
"""


class RestoreWorkflowError(Exception):
    """恢复工作流错误基类"""
    pass


class InvalidRestoreJobError(RestoreWorkflowError):
    """无效的恢复任务"""
    pass


class InvalidRestorePolicyError(RestoreWorkflowError):
    """无效的恢复策略"""
    pass


class RestoreExecutorError(RestoreWorkflowError):
    """恢复执行器错误"""
    pass


class RestoreExecutorNotFoundError(RestoreWorkflowError):
    """恢复执行器未找到"""
    def __init__(self, executor_type: str):
        super().__init__(f"Restore executor not found: {executor_type}")


class RestoreExecutorAlreadyExistsError(RestoreWorkflowError):
    """恢复执行器已存在"""
    def __init__(self, executor_type: str):
        super().__init__(f"Restore executor already registered: {executor_type}")
