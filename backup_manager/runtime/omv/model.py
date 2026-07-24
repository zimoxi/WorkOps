"""
WorkOps OMV Runtime Model — OMV 运行时模型
Sprint060: OMV API Runtime Foundation

OMVRuntimeMode, OMVRuntimeSession
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidOMVRuntimeSessionError


class OMVRuntimeMode(Enum):
    """OMV 运行时模式。"""

    READ_ONLY = "read_only"
    MUTATION = "mutation"


@dataclass(frozen=True, slots=True)
class OMVRuntimeSession:
    """
    OMV 运行时会话。不可变。

    Sprint060: 仅允许 READ_ONLY 模式。
    """

    session_id: str
    adapter_id: str
    mode: OMVRuntimeMode
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidOMVRuntimeSessionError("session_id must be a non-empty string")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidOMVRuntimeSessionError("adapter_id must be a non-empty string")
        if not isinstance(self.mode, OMVRuntimeMode):
            raise InvalidOMVRuntimeSessionError("mode must be an OMVRuntimeMode instance")
        if self.mode == OMVRuntimeMode.MUTATION:
            raise InvalidOMVRuntimeSessionError("MUTATION mode is not allowed in read-only OMV runtime")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
