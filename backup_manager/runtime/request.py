"""
WorkOps Runtime Request — 运行时请求模型
Sprint052: ReadOnly Runtime Connector Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .mode import RuntimeMode
from .errors import InvalidRuntimeRequestError


@dataclass(frozen=True, slots=True)
class RuntimeRequest:
    """
    运行时请求。不可变。

    Sprint052: 仅允许 READ_ONLY 模式。
    """

    execution_id: str
    adapter_id: str
    operation: str
    mode: RuntimeMode
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise InvalidRuntimeRequestError("execution_id must be a non-empty string")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidRuntimeRequestError("adapter_id must be a non-empty string")
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise InvalidRuntimeRequestError("operation must be a non-empty string")
        if not isinstance(self.mode, RuntimeMode):
            raise InvalidRuntimeRequestError("mode must be a RuntimeMode instance")
        if self.mode == RuntimeMode.MUTATION:
            raise InvalidRuntimeRequestError("MUTATION mode is not allowed in read-only runtime")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
