"""
WorkOps PVE Connection — PVE 连接配置和状态
Sprint068: Real PVE API Client

PVEConnectionConfig, PVERuntimeState
"""

from dataclasses import dataclass
from enum import Enum

from .exceptions import PVEConnectionError


class PVERuntimeState(Enum):
    """PVE 运行时状态。"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PVEConnectionConfig:
    """
    PVE 连接配置。不可变。

    不存储凭证。
    """

    host: str
    port: int
    verify_ssl: bool
    timeout_seconds: int

    def __post_init__(self):
        if not isinstance(self.host, str) or not self.host.strip():
            raise PVEConnectionError("host must be a non-empty string")
        if not isinstance(self.port, int) or self.port <= 0:
            raise PVEConnectionError("port must be a positive integer")
        if not isinstance(self.verify_ssl, bool):
            raise PVEConnectionError("verify_ssl must be a bool")
        if not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise PVEConnectionError("timeout_seconds must be a positive integer")
