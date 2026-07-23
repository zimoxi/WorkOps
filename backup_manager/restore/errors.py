"""
WorkOps Restore Errors — 恢复工作流错误
Sprint036: Restore Workflow Foundation
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
