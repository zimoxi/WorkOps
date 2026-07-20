"""
WorkOps Adapter Session — Adapter 会话状态机
Sprint023: Adapter Runtime Integration Foundation

状态转换：CREATED → CONNECTED → CLOSED
禁止保存 client/transport/secret。
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from .errors import AdapterSessionStateError


class SessionState(Enum):
    """会话状态。"""

    CREATED = "created"
    CONNECTED = "connected"
    CLOSED = "closed"


# 允许的状态转换
_VALID_TRANSITIONS = {
    SessionState.CREATED: {SessionState.CONNECTED, SessionState.CLOSED},
    SessionState.CONNECTED: {SessionState.CLOSED},
    SessionState.CLOSED: set(),
}


@dataclass(slots=True)
class AdapterSession:
    """
    Adapter 会话。

    只保存：session_id, adapter_type, device_id, state, timestamps。
    禁止保存：client, paramiko client, socket, transport, secret。
    """

    adapter_type: str
    device_id: str
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: SessionState = field(default=SessionState.CREATED)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    connected_at: datetime | None = field(default=None)
    closed_at: datetime | None = field(default=None)

    def transition(self, new_state: SessionState) -> None:
        """
        状态转换。必须校验合法性。

        Raises:
            AdapterSessionStateError: 非法转换
        """
        allowed = _VALID_TRANSITIONS.get(self.state, set())
        if new_state not in allowed:
            raise AdapterSessionStateError(
                f"Cannot transition from {self.state.value} to {new_state.value}"
            )
        self.state = new_state
        now = datetime.now(timezone.utc)
        if new_state == SessionState.CONNECTED:
            self.connected_at = now
        elif new_state == SessionState.CLOSED:
            self.closed_at = now

    @property
    def is_closed(self) -> bool:
        return self.state == SessionState.CLOSED
