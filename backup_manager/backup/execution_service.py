"""
WorkOps Backup Execution Service — 执行服务
Sprint030: Backup Execution Engine

管理执行生命周期。不执行真实备份操作。
"""

import uuid
from datetime import datetime, timezone

from .execution import BackupExecution
from .state import BackupExecutionState
from .execution_state import validate_transition
from .errors import BackupExecutionError


class BackupExecutionService:
    """
    备份执行服务。

    管理执行生命周期：create → start → complete/fail/cancel。
    不执行真实备份操作。
    """

    def __init__(self):
        self._executions: dict[str, BackupExecution] = {}

    def create_execution(self, job_id: str) -> BackupExecution:
        """
        创建执行记录。

        Args:
            job_id: 关联的任务 ID

        Returns:
            BackupExecution
        """
        execution = BackupExecution(
            execution_id=uuid.uuid4().hex,
            job_id=job_id,
            state=BackupExecutionState.PENDING,
        )
        self._executions[execution.execution_id] = execution
        return execution

    def start_execution(self, execution_id: str) -> BackupExecution:
        """
        开始执行。

        Args:
            execution_id: 执行 ID

        Returns:
            BackupExecution (new state)
        """
        execution = self._get_execution(execution_id)
        validate_transition(execution.state, BackupExecutionState.RUNNING)
        now = datetime.now(timezone.utc)
        updated = BackupExecution(
            execution_id=execution.execution_id,
            job_id=execution.job_id,
            state=BackupExecutionState.RUNNING,
            started_at=now,
            finished_at=None,
            message="",
        )
        self._executions[execution_id] = updated
        return updated

    def complete_execution(self, execution_id: str, message: str = "") -> BackupExecution:
        """
        完成执行。

        Args:
            execution_id: 执行 ID
            message: 完成消息

        Returns:
            BackupExecution (new state)
        """
        execution = self._get_execution(execution_id)
        validate_transition(execution.state, BackupExecutionState.SUCCESS)
        now = datetime.now(timezone.utc)
        updated = BackupExecution(
            execution_id=execution.execution_id,
            job_id=execution.job_id,
            state=BackupExecutionState.SUCCESS,
            started_at=execution.started_at,
            finished_at=now,
            message=message,
        )
        self._executions[execution_id] = updated
        return updated

    def fail_execution(self, execution_id: str, message: str = "") -> BackupExecution:
        """
        执行失败。

        Args:
            execution_id: 执行 ID
            message: 失败消息

        Returns:
            BackupExecution (new state)
        """
        execution = self._get_execution(execution_id)
        validate_transition(execution.state, BackupExecutionState.FAILED)
        now = datetime.now(timezone.utc)
        updated = BackupExecution(
            execution_id=execution.execution_id,
            job_id=execution.job_id,
            state=BackupExecutionState.FAILED,
            started_at=execution.started_at,
            finished_at=now,
            message=message,
        )
        self._executions[execution_id] = updated
        return updated

    def cancel_execution(self, execution_id: str, message: str = "") -> BackupExecution:
        """
        取消执行。

        Args:
            execution_id: 执行 ID
            message: 取消消息

        Returns:
            BackupExecution (new state)
        """
        execution = self._get_execution(execution_id)
        validate_transition(execution.state, BackupExecutionState.CANCELLED)
        now = datetime.now(timezone.utc)
        updated = BackupExecution(
            execution_id=execution.execution_id,
            job_id=execution.job_id,
            state=BackupExecutionState.CANCELLED,
            started_at=execution.started_at,
            finished_at=now,
            message=message,
        )
        self._executions[execution_id] = updated
        return updated

    def get_execution(self, execution_id: str) -> BackupExecution:
        """获取执行记录。"""
        return self._get_execution(execution_id)

    def list_executions(self) -> list[BackupExecution]:
        """返回所有执行记录。"""
        return list(self._executions.values())

    def _get_execution(self, execution_id: str) -> BackupExecution:
        execution = self._executions.get(execution_id)
        if execution is None:
            raise BackupExecutionError(f"Execution not found: {execution_id}")
        return execution
