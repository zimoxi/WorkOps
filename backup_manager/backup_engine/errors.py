"""
WorkOps Backup Engine Errors — 备份引擎错误
Sprint070: Real Backup Execution Engine
"""


class BackupEngineError(Exception):
    """备份引擎错误基类"""
    pass


class InvalidBackupExecutionError(BackupEngineError):
    """无效备份执行"""
    pass


class BackupRuntimeUnavailableError(BackupEngineError):
    """备份运行时不可用"""
    pass


class BackupExecutionTimeoutError(BackupEngineError):
    """备份执行超时"""
    pass
