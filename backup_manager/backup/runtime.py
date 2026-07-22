"""
WorkOps Execution Context — 执行上下文
Sprint032: Safe Executor Runtime

frozen dataclass。
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .errors import ExecutorRuntimeError


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """
    执行上下文。不可变。
    """

    execution_id: str
    timeout_seconds: int = 300
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: tuple = ()

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise ExecutorRuntimeError("execution_id must be a non-empty string")
        if not isinstance(self.timeout_seconds, int) or isinstance(self.timeout_seconds, bool):
            raise ExecutorRuntimeError("timeout_seconds must be an integer")
        if self.timeout_seconds <= 0:
            raise ExecutorRuntimeError("timeout_seconds must be > 0")
        if not isinstance(self.metadata, tuple):
            raise ExecutorRuntimeError("metadata must be a tuple")
