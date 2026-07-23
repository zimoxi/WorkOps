"""
WorkOps Job Scheduler Contract — 作业调度器接口
Sprint039: Job Scheduler Foundation

只定义接口。不执行真实调度。
"""

from abc import ABC, abstractmethod

from .model import Job


class JobScheduler(ABC):
    """
    作业调度器接口。

    只定义接口。不执行真实调度。
    """

    @abstractmethod
    def submit(self, job: Job) -> None:
        """
        提交作业。

        Args:
            job: 作业
        """
        ...

    @abstractmethod
    def get(self, job_id: str) -> Job:
        """
        获取作业。

        Args:
            job_id: 作业 ID

        Returns:
            Job
        """
        ...
