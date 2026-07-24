"""
WorkOps Transaction Errors — 事务错误
Sprint056: Operation Transaction System Foundation
"""


class TransactionError(Exception):
    """事务错误基类"""
    pass


class InvalidTransactionError(TransactionError):
    """无效事务"""
    pass


class TransactionConflictError(TransactionError):
    """事务冲突"""
    def __init__(self, transaction_id: str):
        super().__init__(f"Transaction already exists: {transaction_id}")


class TransactionUnavailableError(TransactionError):
    """事务不可用"""
    pass
