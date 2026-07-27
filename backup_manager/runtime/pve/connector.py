"""
WorkOps PVE API Connector — PVE API 连接器
Sprint059/Sprint068: PVE API Runtime Foundation / Real PVE API Client

PVEAPIConnector: abstract contract
RealPVEAPIConnector: real implementation (contract-level, no real API)
"""

from abc import ABC, abstractmethod

from .model import PVERuntimeSession
from .request import PVEAPIRequest
from .result import PVERuntimeResult
from .connection import PVEConnectionConfig, PVERuntimeState
from .exceptions import PVEConnectionError, PVEReadonlyViolationError
from .readonly import validate_pve_readonly_operation, ALLOWED_READONLY_OPERATIONS


class PVEAPIConnector(ABC):
    """
    PVE API 连接器接口（Sprint059）。

    只定义接口。不实现真实 API 连接。
    """

    @abstractmethod
    def connect(self, session: PVERuntimeSession) -> None:
        """
        建立 PVE API 连接。

        Args:
            session: PVE 运行时会话
        """
        ...

    @abstractmethod
    def execute_readonly(self, request: PVEAPIRequest) -> PVERuntimeResult:
        """
        执行只读 PVE API 命令。

        Args:
            request: PVE API 请求

        Returns:
            PVERuntimeResult
        """
        ...


class RealPVEAPIConnector:
    """
    真实 PVE API 连接器（Sprint068）。

    职责:
    - 建立只读 API 边界
    - 验证操作
    - 映射响应

    不实现真实 API 连接（contract-level）。
    """

    def __init__(self):
        self._state = PVERuntimeState.DISCONNECTED
        self._config: PVEConnectionConfig | None = None

    @property
    def state(self) -> PVERuntimeState:
        """当前连接状态。"""
        return self._state

    def connect(self, config: PVEConnectionConfig) -> None:
        """
        建立 PVE API 连接。

        Args:
            config: PVE 连接配置

        Raises:
            PVEConnectionError: 连接失败
        """
        if not isinstance(config, PVEConnectionConfig):
            raise PVEConnectionError("config must be a PVEConnectionConfig instance")
        self._state = PVERuntimeState.CONNECTING
        # Contract-level: store config, mark connected
        # Real implementation would connect to PVE API here
        self._config = config
        self._state = PVERuntimeState.CONNECTED

    def execute_readonly(self, operation: str) -> dict:
        """
        执行只读操作。

        Args:
            operation: 操作标识符

        Returns:
            dict with operation result

        Raises:
            PVEReadonlyViolationError: 操作不是只读的
            PVEConnectionError: 未连接
        """
        if self._state != PVERuntimeState.CONNECTED:
            raise PVEConnectionError("not connected")
        validate_pve_readonly_operation(operation)
        # Contract-level: return placeholder
        return {
            "operation": operation,
            "status": "contract_only",
            "message": "Real PVE API execution not implemented",
        }

    def close(self) -> None:
        """关闭连接。"""
        self._state = PVERuntimeState.DISCONNECTED
        self._config = None
