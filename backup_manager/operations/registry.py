"""
WorkOps Operation Registry — 操作注册表
Sprint038: Operation Orchestration Foundation

注册操作执行器。不允许覆盖、不允许动态加载。
"""

from .executor import OperationExecutor
from .errors import OperationConflictError, OperationNotFoundError


class OperationRegistry:
    """
    操作注册表。

    不允许覆盖已注册操作。
    """

    def __init__(self):
        self._executors: dict[str, OperationExecutor] = {}

    def register(self, operation_type: str, executor: OperationExecutor) -> None:
        """
        注册操作执行器。

        Args:
            operation_type: 操作类型标识
            executor: 执行器实例

        Raises:
            OperationConflictError: 重复注册
        """
        if not isinstance(operation_type, str) or not operation_type.strip():
            raise TypeError("operation_type must be a non-empty string")
        if not isinstance(executor, OperationExecutor):
            raise TypeError("executor must be an OperationExecutor instance")
        if operation_type in self._executors:
            raise OperationConflictError(operation_type)
        self._executors[operation_type] = executor

    def get(self, operation_type: str) -> OperationExecutor:
        """
        获取操作执行器。

        Args:
            operation_type: 操作类型标识

        Returns:
            OperationExecutor

        Raises:
            OperationNotFoundError: 未注册
        """
        executor = self._executors.get(operation_type)
        if executor is None:
            raise OperationNotFoundError(operation_type)
        return executor

    def list(self) -> list[str]:
        """返回所有已注册类型。"""
        return list(self._executors.keys())

    def supports(self, operation_type: str) -> bool:
        """检查类型是否已注册。"""
        return operation_type in self._executors
