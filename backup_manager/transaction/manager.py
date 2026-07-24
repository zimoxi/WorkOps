"""
WorkOps Transaction Manager Contract — 事务管理器接口
Sprint056: Operation Transaction System Foundation

只定义接口。不实现持久化。
"""

from abc import ABC, abstractmethod

from .model import OperationTransaction


class TransactionManager(ABC):
    """
    事务管理器接口。

    只定义接口。不实现持久化。
    """

    @abstractmethod
    def begin(self, operation_id: str, job_id: str) -> OperationTransaction:
        """
        开始事务。

        Args:
            operation_id: 操作 ID
            job_id: 作业 ID

        Returns:
            OperationTransaction
        """
        ...

    @abstractmethod
    def complete(self, transaction: OperationTransaction) -> OperationTransaction:
        """
        完成事务。

        Args:
            transaction: 操作事务

        Returns:
            OperationTransaction
        """
        ...

    @abstractmethod
    def fail(self, transaction: OperationTransaction) -> OperationTransaction:
        """
        事务失败。

        Args:
            transaction: 操作事务

        Returns:
            OperationTransaction
        """
        ...
