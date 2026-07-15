"""
WorkOps Persistence Errors — 错误定义
Sprint020: Persistence Foundation
"""


class PersistenceError(Exception):
    """Persistence 错误基类"""
    pass


class PersistenceValidationError(PersistenceError):
    """输入校验错误"""
    pass


class RepositoryConflictError(PersistenceError):
    """ID 冲突或内容冲突"""
    pass


class SchemaNotReadyError(PersistenceError):
    """Schema 未准备"""
    pass


class MigrationError(PersistenceError):
    """Migration 错误"""
    pass


class MigrationSafetyError(MigrationError):
    """downgrade 安全检查失败"""
    pass


class SchemaConflictError(MigrationError):
    """未登记表冲突"""
    pass
