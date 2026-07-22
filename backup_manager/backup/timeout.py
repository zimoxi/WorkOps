"""
WorkOps Execution Timeout — 执行超时模型
Sprint032: Safe Executor Runtime
"""

from .errors import ExecutorRuntimeError


class ExecutionTimeout:
    """
    执行超时。不可变。

    timeout_seconds 必须 > 0。
    """

    __slots__ = ("_timeout_seconds",)

    def __init__(self, timeout_seconds: int):
        if not isinstance(timeout_seconds, int) or isinstance(timeout_seconds, bool):
            raise ExecutorRuntimeError("timeout_seconds must be an integer")
        if timeout_seconds <= 0:
            raise ExecutorRuntimeError("timeout_seconds must be > 0")
        self._timeout_seconds = timeout_seconds

    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds

    def __repr__(self) -> str:
        return f"ExecutionTimeout(timeout_seconds={self._timeout_seconds})"
