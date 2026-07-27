"""
WorkOps OMV API Connector — OMV API 连接器
Sprint060/Sprint069: OMV API Runtime Foundation / Real OMV API Client

OMVAPIConnector: abstract contract
RealOMVAPIConnector: real implementation (contract-level, no real API)
"""

from abc import ABC, abstractmethod

from .model import OMVRuntimeSession
from .request import OMVAPIRequest
from .result import OMVRuntimeResult
from .connection import OMVConnectionConfig, OMVRuntimeState
from .exceptions import OMVConnectionError, OMVReadonlyViolationError
from .readonly import validate_omv_readonly_operation, ALLOWED_READONLY_OPERATIONS


class OMVAPIConnector(ABC):
    """
    OMV API 连接器接口（Sprint060）。

    只定义接口。不实现真实 API 连接。
    """

    @abstractmethod
    def connect(self, session: OMVRuntimeSession) -> None:
        """
        建立 OMV API 连接。

        Args:
            session: OMV 运行时会话
        """
        ...

    @abstractmethod
    def execute_readonly(self, request: OMVAPIRequest) -> OMVRuntimeResult:
        """
        执行只读 OMV API 命令。

        Args:
            request: OMV API 请求

        Returns:
            OMVRuntimeResult
        """
        ...


class RealOMVAPIConnector:
    """
    真实 OMV API 连接器（Sprint069）。

    职责:
    - 建立只读 API 边界
    - 验证操作
    - 映射响应

    不实现真实 API 连接（contract-level）。
    """

    def __init__(self):
        self._state = OMVRuntimeState.DISCONNECTED
        self._config: OMVConnectionConfig | None = None

    @property
    def state(self) -> OMVRuntimeState:
        """当前连接状态。"""
        return self._state

    def connect(self, config: OMVConnectionConfig) -> None:
        """
        建立 OMV API 连接。

        Args:
            config: OMV 连接配置

        Raises:
            OMVConnectionError: 连接失败
        """
        if not isinstance(config, OMVConnectionConfig):
            raise OMVConnectionError("config must be an OMVConnectionConfig instance")
        self._state = OMVRuntimeState.CONNECTING
        # Contract-level: store config, mark connected
        # Real implementation would connect to OMV API here
        self._config = config
        self._state = OMVRuntimeState.CONNECTED

    def execute_readonly(self, operation: str) -> dict:
        """
        执行只读操作。

        Args:
            operation: 操作标识符

        Returns:
            dict with operation result

        Raises:
            OMVReadonlyViolationError: 操作不是只读的
            OMVConnectionError: 未连接
        """
        if self._state != OMVRuntimeState.CONNECTED:
            raise OMVConnectionError("not connected")
        validate_omv_readonly_operation(operation)
        # Contract-level: return placeholder
        return {
            "operation": operation,
            "status": "contract_only",
            "message": "Real OMV API execution not implemented",
        }

    def close(self) -> None:
        """关闭连接。"""
        self._state = OMVRuntimeState.DISCONNECTED
        self._config = None
