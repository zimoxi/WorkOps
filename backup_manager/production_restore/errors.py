"""
WorkOps Production Restore Errors — 生产恢复错误
Sprint062: Production Restore Execution Foundation
"""


class ProductionRestoreError(Exception):
    """生产恢复错误基类"""
    pass


class InvalidProductionRestoreRequestError(ProductionRestoreError):
    """无效生产恢复请求"""
    pass


class RestoreRuntimeDispatchError(ProductionRestoreError):
    """恢复运行时分发错误"""
    pass


class ProductionRestoreUnavailableError(ProductionRestoreError):
    """生产恢复不可用"""
    pass
