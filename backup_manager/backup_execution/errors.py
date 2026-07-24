"""
WorkOps Backup Execution Errors — 备份执行错误
Sprint053: Backup Execution Pipeline Foundation
"""


class BackupExecutionError(Exception):
    """备份执行错误基类"""
    pass


class InvalidBackupExecutionRequestError(BackupExecutionError):
    """无效备份执行请求"""
    pass


class BackupExecutionConflictError(BackupExecutionError):
    """备份执行冲突"""
    def __init__(self, backup_id: str):
        super().__init__(f"Backup execution already exists: {backup_id}")


class BackupExecutionUnavailableError(BackupExecutionError):
    """备份执行不可用"""
    pass
