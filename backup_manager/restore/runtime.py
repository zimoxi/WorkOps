"""
WorkOps Restore Runtime Contract — 恢复运行时接口
Sprint037: Restore Execution Framework

定义恢复运行时接口。不实现真实恢复。
"""

from abc import ABC, abstractmethod


class RestoreRuntime(ABC):
    """
    恢复运行时接口。

    只定义接口。不实现真实恢复。
    """

    @abstractmethod
    def prepare(self) -> None:
        """准备恢复环境。"""
        ...

    @abstractmethod
    def execute(self) -> dict:
        """
        执行恢复。

        Returns:
            dict: 恢复结果
        """
        ...

    @abstractmethod
    def cleanup(self) -> None:
        """清理恢复环境。"""
        ...
