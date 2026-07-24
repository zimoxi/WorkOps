"""
WorkOps Production Backup Errors — 生产备份错误
Sprint061: Production Backup Execution Foundation
"""


class ProductionBackupError(Exception):
    """生产备份错误基类"""
    pass


class InvalidProductionBackupRequestError(ProductionBackupError):
    """无效生产备份请求"""
    pass


class BackupRuntimeDispatchError(ProductionBackupError):
    """备份运行时分发错误"""
    pass


class ProductionBackupUnavailableError(ProductionBackupError):
    """生产备份不可用"""
    pass
