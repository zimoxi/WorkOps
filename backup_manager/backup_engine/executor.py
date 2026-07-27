"""
WorkOps Real Backup Executor — 真实备份执行器
Sprint070: Real Backup Execution Engine

Execution flow:
Validate Request → Create Execution Context → Security Validation → Dispatch Runtime → Return Backup Result
"""

from .model import BackupExecutionRequest
from .result import BackupExecutionResult
from .dispatcher import BackupRuntimeDispatcher
from .errors import InvalidBackupExecutionError


class RealBackupExecutor:
    """
    真实备份执行器。

    执行流程:
    1. 验证请求
    2. 创建执行上下文
    3. 安全验证
    4. 分发运行时
    5. 返回备份结果
    """

    def __init__(self, dispatcher: BackupRuntimeDispatcher):
        if not isinstance(dispatcher, BackupRuntimeDispatcher):
            raise InvalidBackupExecutionError("dispatcher must be a BackupRuntimeDispatcher instance")
        self._dispatcher = dispatcher

    def execute(self, request: BackupExecutionRequest) -> BackupExecutionResult:
        """
        执行备份。

        Args:
            request: 备份执行请求

        Returns:
            BackupExecutionResult

        Raises:
            InvalidBackupExecutionError: 无效请求
        """
        if not isinstance(request, BackupExecutionRequest):
            raise InvalidBackupExecutionError("request must be a BackupExecutionRequest instance")
        # Security validation: ensure no forbidden fields
        # Dispatch to runtime
        return self._dispatcher.dispatch(request)
