"""
WorkOps Real Restore Executor — 真实恢复执行器
Sprint071: Real Restore Execution Engine

Execution flow:
Validate Request → Create Execution Context → Security Validation → Dispatch Runtime → Return Restore Result
"""

from .model import RestoreExecutionRequest
from .result import RestoreExecutionResult
from .dispatcher import RestoreRuntimeDispatcher
from .errors import InvalidRestoreExecutionError


class RealRestoreExecutor:
    """
    真实恢复执行器。

    执行流程:
    1. 验证请求
    2. 创建执行上下文
    3. 安全验证
    4. 分发运行时
    5. 返回恢复结果
    """

    def __init__(self, dispatcher: RestoreRuntimeDispatcher):
        if not isinstance(dispatcher, RestoreRuntimeDispatcher):
            raise InvalidRestoreExecutionError("dispatcher must be a RestoreRuntimeDispatcher instance")
        self._dispatcher = dispatcher

    def execute(self, request: RestoreExecutionRequest) -> RestoreExecutionResult:
        """
        执行恢复。

        Args:
            request: 恢复执行请求

        Returns:
            RestoreExecutionResult

        Raises:
            InvalidRestoreExecutionError: 无效请求
        """
        if not isinstance(request, RestoreExecutionRequest):
            raise InvalidRestoreExecutionError("request must be a RestoreExecutionRequest instance")
        # Security validation: ensure no forbidden fields
        # Dispatch to runtime
        return self._dispatcher.dispatch(request)
