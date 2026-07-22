"""
WorkOps Process Runner Contract — 进程运行器接口
Sprint033: Rsync Executor Foundation

定义进程运行器接口。不实现真实 subprocess。
"""

from abc import ABC, abstractmethod


class ProcessRunner(ABC):
    """
    进程运行器接口。

    只定义接口。不实现真实 subprocess。
    """

    @abstractmethod
    def run(self, command) -> dict:
        """
        运行命令。

        Args:
            command: 命令对象

        Returns:
            dict: 执行结果
        """
        ...
