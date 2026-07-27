"""
WorkOps OMV Connection — OMV 连接配置和状态
Sprint069: Real OMV API Client

OMVConnectionConfig, OMVRuntimeState
"""

from dataclasses import dataclass
from enum import Enum

from .exceptions import OMVConnectionError


class OMVRuntimeState(Enum):
    """OMV 运行时状态。"""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class OMVConnectionConfig:
    """
    OMV 连接配置。不可变。

    不存储凭证。
    """

    host: str
    port: int
    verify_ssl: bool
    timeout_seconds: int

    def __post_init__(self):
        if not isinstance(self.host, str) or not self.host.strip():
            raise OMVConnectionError("host must be a non-empty string")
        if not isinstance(self.port, int) or self.port <= 0:
            raise OMVConnectionError("port must be a positive integer")
        if not isinstance(self.verify_ssl, bool):
            raise OMVConnectionError("verify_ssl must be a bool")
        if not isinstance(self.timeout_seconds, int) or self.timeout_seconds <= 0:
            raise OMVConnectionError("timeout_seconds must be a positive integer")
