"""
WorkOps Health Execution Model — 健康执行模型
Sprint055: Health Runtime Integration Foundation

HealthExecutionStatus enum
"""

from enum import Enum


class HealthExecutionStatus(Enum):
    """健康执行状态。"""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
