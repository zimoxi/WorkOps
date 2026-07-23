"""
WorkOps Restore Executor Registry — 恢复执行器注册表
Sprint037: Restore Execution Framework

注册恢复执行器。不允许覆盖、不允许动态加载。
"""

from .executor import RestoreExecutor
from .errors import RestoreExecutorNotFoundError, RestoreExecutorAlreadyExistsError


class RestoreExecutorRegistry:
    """
    恢复执行器注册表。

    不允许覆盖已注册执行器。
    """

    def __init__(self):
        self._executors: dict[str, RestoreExecutor] = {}

    def register(self, executor_type: str, executor: RestoreExecutor) -> None:
        """
        注册执行器。

        Args:
            executor_type: 执行器类型标识
            executor: 执行器实例

        Raises:
            RestoreExecutorAlreadyExistsError: 重复注册
        """
        if not isinstance(executor_type, str) or not executor_type.strip():
            raise TypeError("executor_type must be a non-empty string")
        if not isinstance(executor, RestoreExecutor):
            raise TypeError("executor must be a RestoreExecutor instance")
        if executor_type in self._executors:
            raise RestoreExecutorAlreadyExistsError(executor_type)
        self._executors[executor_type] = executor

    def get(self, executor_type: str) -> RestoreExecutor:
        """
        获取执行器。

        Args:
            executor_type: 执行器类型标识

        Returns:
            RestoreExecutor

        Raises:
            RestoreExecutorNotFoundError: 未注册
        """
        executor = self._executors.get(executor_type)
        if executor is None:
            raise RestoreExecutorNotFoundError(executor_type)
        return executor

    def list(self) -> list[str]:
        """返回所有已注册类型。"""
        return list(self._executors.keys())

    def supports(self, executor_type: str) -> bool:
        """检查类型是否已注册。"""
        return executor_type in self._executors
