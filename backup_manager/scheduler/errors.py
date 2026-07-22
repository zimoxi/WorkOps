"""
WorkOps Scheduler Errors — 调度器错误
Sprint035: Backup Scheduler Foundation
"""


class SchedulerError(Exception):
    """调度器错误基类"""
    pass


class InvalidScheduleError(SchedulerError):
    """无效的调度配置"""
    pass
