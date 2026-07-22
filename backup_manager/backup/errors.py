"""
WorkOps Backup Workflow Errors — 备份工作流错误
Sprint029: Backup Workflow Foundation
"""


class BackupWorkflowError(Exception):
    """备份工作流错误基类"""
    pass


class InvalidBackupJobError(BackupWorkflowError):
    """无效的备份任务"""
    pass


class InvalidPolicyError(BackupWorkflowError):
    """无效的备份策略"""
    pass


class BackupExecutionError(BackupWorkflowError):
    """备份执行错误"""
    pass


class InvalidStateTransitionError(BackupWorkflowError):
    """非法状态转换"""
    def __init__(self, current: str, target: str):
        super().__init__(f"Invalid state transition: {current} -> {target}")
