"""
WorkOps Backup Workflow Errors — 备份工作流错误
Sprint041: Backup Workflow Foundation v1
"""


class BackupWorkflowError(Exception):
    """备份工作流错误基类"""
    pass


class InvalidBackupRequestError(BackupWorkflowError):
    """无效备份请求"""
    pass


class BackupConflictError(BackupWorkflowError):
    """备份冲突"""
    def __init__(self, backup_id: str):
        super().__init__(f"Backup already exists: {backup_id}")


class BackupNotFoundError(BackupWorkflowError):
    """备份未找到"""
    def __init__(self, backup_id: str):
        super().__init__(f"Backup not found: {backup_id}")
