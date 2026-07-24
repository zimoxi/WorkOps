"""
WorkOps Runtime Result — 运行时结果模型
Sprint052: ReadOnly Runtime Connector Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidRuntimeRequestError


@dataclass(frozen=True, slots=True)
class RuntimeResult:
    """
    运行时结果。不可变。
    """

    execution_id: str
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise InvalidRuntimeRequestError("execution_id must be a non-empty string")
        if not isinstance(self.success, bool):
            raise InvalidRuntimeRequestError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidRuntimeRequestError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
