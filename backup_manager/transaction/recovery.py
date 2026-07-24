"""
WorkOps Recovery — 恢复动作和恢复契约
Sprint056: Operation Transaction System Foundation
"""

from enum import Enum
from abc import ABC, abstractmethod

from .model import OperationTransaction


class RecoveryAction(Enum):
    """恢复动作。"""

    NONE = "none"
    RETRY = "retry"
    ABORT = "abort"


class RecoveryContract(ABC):
    """
    恢复契约接口。

    只定义接口。不实现真实恢复。
    """

    @abstractmethod
    def recover(self, transaction: OperationTransaction) -> RecoveryAction:
        """
        恢复事务。

        Args:
            transaction: 操作事务

        Returns:
            RecoveryAction
        """
        ...
