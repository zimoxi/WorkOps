"""
WorkOps Job Errors — 作业调度错误
Sprint039: Job Scheduler Foundation
"""


class JobError(Exception):
    """作业错误基类"""
    pass


class InvalidJobError(JobError):
    """无效作业"""
    pass


class JobConflictError(JobError):
    """作业冲突"""
    def __init__(self, job_id: str):
        super().__init__(f"Job already exists: {job_id}")


class JobNotFoundError(JobError):
    """作业未找到"""
    def __init__(self, job_id: str):
        super().__init__(f"Job not found: {job_id}")
