"""
WorkOps Operation Errors — 操作编排错误
Sprint038: Operation Orchestration Foundation
"""


class OperationError(Exception):
    """操作错误基类"""
    pass


class InvalidOperationError(OperationError):
    """无效操作"""
    pass


class OperationConflictError(OperationError):
    """操作冲突"""
    def __init__(self, operation_id: str):
        super().__init__(f"Operation already exists: {operation_id}")


class OperationNotFoundError(OperationError):
    """操作未找到"""
    def __init__(self, operation_id: str):
        super().__init__(f"Operation not found: {operation_id}")
