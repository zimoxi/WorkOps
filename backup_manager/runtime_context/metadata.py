"""
WorkOps Execution Metadata — 执行元数据
Sprint051: Adapter Execution Context Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidExecutionContextError


@dataclass(frozen=True, slots=True)
class ExecutionMetadata:
    """
    执行元数据。不可变。
    """

    execution_id: str
    operation_id: str
    adapter_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise InvalidExecutionContextError("execution_id must be a non-empty string")
        if not isinstance(self.operation_id, str) or not self.operation_id.strip():
            raise InvalidExecutionContextError("operation_id must be a non-empty string")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidExecutionContextError("adapter_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
