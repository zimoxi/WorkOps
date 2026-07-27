"""
WorkOps Linux SSH Connector — Linux SSH 连接器
Sprint058/Sprint067: Linux SSH Runtime Foundation / Real Linux SSH Connector

LinuxSSHConnector: abstract contract
RealLinuxSSHConnector: real implementation (contract-level, no real SSH)
"""

from abc import ABC, abstractmethod

from .model import SSHSession
from .session import SSHExecutionRequest
from .result import SSHRuntimeResult
from .connection import SSHConnectionConfig, SSHConnectionState
from .exceptions import SSHConnectionError, SSHReadonlyViolationError
from .readonly import validate_readonly_operation, ALLOWED_READONLY_OPERATIONS


class LinuxSSHConnector(ABC):
    """
    Linux SSH 连接器接口（Sprint058）。

    只定义接口。不实现真实 SSH 连接。
    """

    @abstractmethod
    def connect(self, session: SSHSession) -> None:
        """
        建立 SSH 连接。

        Args:
            session: SSH 会话
        """
        ...

    @abstractmethod
    def execute_readonly(self, request: SSHExecutionRequest) -> SSHRuntimeResult:
        """
        执行只读 SSH 命令。

        Args:
            request: SSH 执行请求

        Returns:
            SSHRuntimeResult
        """
        ...


class RealLinuxSSHConnector:
    """
    真实 Linux SSH 连接器（Sprint067）。

    职责:
    - 创建只读连接
    - 验证操作
    - 返回运行时结果

    不实现真实 SSH 连接（contract-level）。
    """

    def __init__(self):
        self._state = SSHConnectionState.DISCONNECTED
        self._config: SSHConnectionConfig | None = None

    @property
    def state(self) -> SSHConnectionState:
        """当前连接状态。"""
        return self._state

    def connect(self, config: SSHConnectionConfig) -> None:
        """
        建立 SSH 连接。

        Args:
            config: SSH 连接配置

        Raises:
            SSHConnectionError: 连接失败
        """
        if not isinstance(config, SSHConnectionConfig):
            raise SSHConnectionError("config must be an SSHConnectionConfig instance")
        self._state = SSHConnectionState.CONNECTING
        # Contract-level: store config, mark connected
        # Real implementation would SSH here
        self._config = config
        self._state = SSHConnectionState.CONNECTED

    def execute_readonly(self, operation: str) -> dict:
        """
        执行只读操作。

        Args:
            operation: 操作标识符

        Returns:
            dict with operation result

        Raises:
            SSHReadonlyViolationError: 操作不是只读的
            SSHConnectionError: 未连接
        """
        if self._state != SSHConnectionState.CONNECTED:
            raise SSHConnectionError("not connected")
        validate_readonly_operation(operation)
        # Contract-level: return placeholder
        return {
            "operation": operation,
            "status": "contract_only",
            "message": "Real SSH execution not implemented",
        }

    def close(self) -> None:
        """关闭连接。"""
        self._state = SSHConnectionState.DISCONNECTED
        self._config = None
