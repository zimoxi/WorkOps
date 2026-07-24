"""
WorkOps OMV Runtime Result — OMV 运行时结果
Sprint060: OMV API Runtime Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidOMVRuntimeSessionError


@dataclass(frozen=True, slots=True)
class OMVRuntimeResult:
    """
    OMV 运行时结果。不可变。
    """

    session_id: str
    success: bool
    message: str
    completed_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidOMVRuntimeSessionError("session_id must be a non-empty string")
        if not isinstance(self.success, bool):
            raise InvalidOMVRuntimeSessionError("success must be a bool")
        if not isinstance(self.message, str):
            raise InvalidOMVRuntimeSessionError("message must be a string")
        if self.completed_at is None:
            object.__setattr__(self, "completed_at", datetime.now(timezone.utc))
