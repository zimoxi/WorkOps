"""
WorkOps Operation Transaction — 操作事务模型
Sprint056: Operation Transaction System Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .status import TransactionStatus
from .errors import InvalidTransactionError


@dataclass(frozen=True, slots=True)
class OperationTransaction:
    """
    操作事务。不可变。
    """

    transaction_id: str
    operation_id: str
    job_id: str
    status: TransactionStatus
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.transaction_id, str) or not self.transaction_id.strip():
            raise InvalidTransactionError("transaction_id must be a non-empty string")
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidTransactionError("operation_id must be a non-empty string")
        if not isinstance(self.job_id, str) or not self.job_id.strip():
            raise InvalidTransactionError("job_id must be a non-empty string")
        if not isinstance(self.status, TransactionStatus):
            raise InvalidTransactionError("status must be a TransactionStatus instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
