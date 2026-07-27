"""
WorkOps SSH Connection — SSH 连接配置和状态
Sprint067: Real Linux SSH Connector

SSHConnectionConfig, SSHConnectionState
"""

from dataclasses import dataclass
from enum import Enum

from .exceptions import SSHConnectionError


class SSHConnectionState(Enum):
    """SSH 连接状态。"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class SSHConnectionConfig:
    """
    SSH 连接配置。不可变。

    不存储凭证。
    """

    host: str
    port: int
    username: str
    timeout_seconds: int

    def __post_init__(self):
        if not isinstance(self.host, str) or not self.host.strip():
            raise SSHConnectionError("host must be a non-empty string")
        if not isinstance(self.port, int) or self.port <= 0:
            raise SSHConnectionError("port must be a positive integer")
        if not isinstance(self.username, str) or not self.username.strip():
            raise SSHConnectionError("username must be a non-empty string")
        if not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise SSHConnectionError("timeout_seconds must be a positive integer")
