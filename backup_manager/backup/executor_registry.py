"""
WorkOps Backup Executor Registry — 执行器注册表
Sprint031: Backup Executor Framework

注册备份执行器。不允许覆盖、不允许动态加载。
"""

from .executor import BackupExecutor
from .errors import ExecutorNotFoundError, ExecutorAlreadyExistsError


class BackupExecutorRegistry:
    """
    备份执行器注册表。

    不允许覆盖已注册执行器。
    """

    def __init__(self):
        self._executors: dict[str, BackupExecutor] = {}

    def register(self, executor_type: str, executor: BackupExecutor) -> None:
        """
        注册执行器。

        Args:
            executor_type: 执行器类型标识
            executor: 执行器实例

        Raises:
            ExecutorAlreadyExistsError: 重复注册
        """
        if not isinstance(executor_type, str) or not executor_type.strip():
            raise TypeError("executor_type must be a non-empty string")
        if not isinstance(executor, BackupExecutor):
            raise TypeError("executor must be a BackupExecutor instance")
        if executor_type in self._executors:
            raise ExecutorAlreadyExistsError(executor_type)
        self._executors[executor_type] = executor

    def get(self, executor_type: str) -> BackupExecutor:
        """
        获取执行器。

        Args:
            executor_type: 执行器类型标识

        Returns:
            BackupExecutor

        Raises:
            ExecutorNotFoundError: 未注册
        """
        executor = self._executors.get(executor_type)
        if executor is None:
            raise ExecutorNotFoundError(executor_type)
        return executor

    def list(self) -> list[str]:
        """返回所有已注册类型。"""
        return list(self._executors.keys())

    def supports(self, executor_type: str) -> bool:
        """检查类型是否已注册。"""
        return executor_type in self._executors
