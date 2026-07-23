"""
WorkOps Restore Execution — 恢复执行模型
Sprint036: Restore Workflow Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime

from .state import RestoreExecutionState
from .errors import RestoreWorkflowError


@dataclass(frozen=True, slots=True)
class RestoreExecution:
    """
    恢复执行记录。不可变。
    """

    execution_id: str
    restore_id: str
    state: RestoreExecutionState = RestoreExecutionState.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str = ""

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise RestoreWorkflowError("execution_id must be a non-empty string")
        if not isinstance(self.restore_id, str) or not self.restore_id.strip():
            raise RestoreWorkflowError("restore_id must be a non-empty string")
        if not isinstance(self.state, RestoreExecutionState):
            raise RestoreWorkflowError("state must be a RestoreExecutionState instance")
        if self.started_at is not None and not isinstance(self.started_at, datetime):
            raise RestoreWorkflowError("started_at must be a datetime or None")
        if self.finished_at is not None and not isinstance(self.finished_at, datetime):
            raise RestoreWorkflowError("finished_at must be a datetime or None")
        if not isinstance(self.message, str):
            raise RestoreWorkflowError("message must be a string")
