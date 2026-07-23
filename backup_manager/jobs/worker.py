"""
WorkOps Job Worker Contract — 作业工作器接口
Sprint039: Job Scheduler Foundation

只定义接口。不执行真实操作。
"""

from abc import ABC, abstractmethod

from .model import Job


class JobWorker(ABC):
    """
    作业工作器接口。

    只定义接口。不执行真实操作。
    """

    @abstractmethod
    def execute(self, job: Job) -> dict:
        """
        执行作业。

        Args:
            job: 作业

        Returns:
            dict: 执行结果
        """
        ...
