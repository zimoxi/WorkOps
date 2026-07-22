"""
WorkOps Backup Execution State Machine — 执行状态转换
Sprint030: Backup Execution Engine
"""

from .state import BackupExecutionState
from .errors import InvalidStateTransitionError


# 允许的状态转换
_VALID_TRANSITIONS = {
    BackupExecutionState.PENDING: {
        BackupExecutionState.RUNNING,
    },
    BackupExecutionState.RUNNING: {
        BackupExecutionState.SUCCESS,
        BackupExecutionState.FAILED,
        BackupExecutionState.CANCELLED,
    },
    BackupExecutionState.SUCCESS: set(),
    BackupExecutionState.FAILED: set(),
    BackupExecutionState.CANCELLED: set(),
}


def validate_transition(current: BackupExecutionState, target: BackupExecutionState) -> None:
    """
    校验状态转换合法性。

    Args:
        current: 当前状态
        target: 目标状态

    Raises:
        InvalidStateTransitionError: 非法转换
    """
    allowed = _VALID_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(current.value, target.value)
