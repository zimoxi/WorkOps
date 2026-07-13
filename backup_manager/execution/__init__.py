"""
WorkOps Execution Engine
Sprint018: Execution Engine Foundation

建立 Execution Engine 基础
打通仅使用 MockAdapter 的执行链
"""

from .errors import (
    ExecutionError,
    TaskNotFoundError,
    InvalidTaskStateError,
    TaskStateTransitionError,
)
from .result import ExecutionResult
from .context import ExecutionContext
from .service import ExecutionService

__all__ = [
    "ExecutionError",
    "TaskNotFoundError",
    "InvalidTaskStateError",
    "TaskStateTransitionError",
    "ExecutionResult",
    "ExecutionContext",
    "ExecutionService",
]
