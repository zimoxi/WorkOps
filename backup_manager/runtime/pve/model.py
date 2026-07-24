"""
WorkOps PVE Runtime Model — PVE 运行时模型
Sprint059: PVE API Runtime Foundation

PVERuntimeMode, PVERuntimeSession
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidPVERuntimeSessionError


class PVERuntimeMode(Enum):
    """PVE 运行时模式。"""

    READ_ONLY = "read_only"
    MUTATION = "mutation"


@dataclass(frozen=True, slots=True)
class PVERuntimeSession:
    """
    PVE 运行时会话。不可变。

    Sprint059: 仅允许 READ_ONLY 模式。
    """

    session_id: str
    adapter_id: str
    mode: PVERuntimeMode
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidPVERuntimeSessionError("session_id must be a non-empty string")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidPVERuntimeSessionError("adapter_id must be a non-empty string")
        if not isinstance(self.mode, PVERuntimeMode):
            raise InvalidPVERuntimeSessionError("mode must be a PVERuntimeMode instance")
        if self.mode == PVERuntimeMode.MUTATION:
            raise InvalidPVERuntimeSessionError("MUTATION mode is not allowed in read-only PVE runtime")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
