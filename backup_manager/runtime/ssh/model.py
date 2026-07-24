"""
WorkOps SSH Session Model — SSH 会话模型
Sprint058: Linux SSH Runtime Foundation

SSHSessionMode, SSHSession
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidSSHSessionError


class SSHSessionMode(Enum):
    """SSH 会话模式。"""

    READ_ONLY = "read_only"
    MUTATION = "mutation"


@dataclass(frozen=True, slots=True)
class SSHSession:
    """
    SSH 会话。不可变。

    Sprint058: 仅允许 READ_ONLY 模式。
    """

    session_id: str
    adapter_id: str
    mode: SSHSessionMode
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidSSHSessionError("session_id must be a non-empty string")
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidSSHSessionError("adapter_id must be a non-empty string")
        if not isinstance(self.mode, SSHSessionMode):
            raise InvalidSSHSessionError("mode must be an SSHSessionMode instance")
        if self.mode == SSHSessionMode.MUTATION:
            raise InvalidSSHSessionError("MUTATION mode is not allowed in read-only SSH runtime")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
