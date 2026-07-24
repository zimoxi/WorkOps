"""
WorkOps Transaction Domain — 事务域
Sprint056: Operation Transaction System Foundation
"""

from .errors import (
    TransactionError,
    InvalidTransactionError,
    TransactionConflictError,
    TransactionUnavailableError,
)
from .status import TransactionStatus
from .model import OperationTransaction
from .retry import RetryPolicy
from .recovery import RecoveryAction, RecoveryContract
from .manager import TransactionManager

__all__ = [
    "TransactionError",
    "InvalidTransactionError",
    "TransactionConflictError",
    "TransactionUnavailableError",
    "TransactionStatus",
    "OperationTransaction",
    "RetryPolicy",
    "RecoveryAction",
    "RecoveryContract",
    "TransactionManager",
]
