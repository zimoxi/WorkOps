"""
WorkOps Executor Runtime Contract — 执行运行时接口
Sprint032: Safe Executor Runtime

定义执行运行时接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .runtime import ExecutionContext


class ExecutorRuntime(ABC):
    """
    执行运行时接口。

    只定义接口。不实现真实执行。
    """

    @abstractmethod
    def prepare(self, context: ExecutionContext) -> None:
        """
        准备执行环境。

        Args:
            context: 执行上下文
        """
        ...

    @abstractmethod
    def collect(self) -> dict:
        """
        收集执行结果。

        Returns:
            dict: 执行结果
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """清理执行环境。"""
        ...
