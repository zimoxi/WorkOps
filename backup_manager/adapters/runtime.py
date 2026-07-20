"""
WorkOps Adapter Runtime — 生命周期管理
Sprint023: Adapter Runtime Integration Foundation

生命周期：create_session → connect → query → close
close 幂等，释放 adapter。
异常不泄漏 secret/credential/connection string。
"""

from datetime import datetime, timezone

from .registry import AdapterRegistry
from .result import AdapterQueryResult
from .session import AdapterSession, SessionState
from .errors import AdapterSessionStateError


class AdapterRuntime:
    """
    Adapter Runtime 管理器。

    管理会话生命周期，不保存任何 secret/credential。
    """

    def __init__(self, registry: AdapterRegistry):
        self._registry = registry
        self._sessions: dict[str, AdapterSession] = {}
        self._adapters: dict[str, object] = {}  # session_id → adapter instance

    def create_session(self, adapter_type: str, device_id: str) -> AdapterSession:
        """
        创建新会话。

        Args:
            adapter_type: Adapter 类型（必须已注册）
            device_id: 设备标识

        Returns:
            AdapterSession

        Raises:
            AdapterNotRegisteredError: 类型未注册
        """
        self._registry.get_descriptor(adapter_type)  # validates type exists
        session = AdapterSession(adapter_type=adapter_type, device_id=device_id)
        self._sessions[session.session_id] = session
        return session

    def connect(self, session_id: str, config: dict = None, **kwargs) -> None:
        """
        连接设备。会话必须处于 CREATED 状态。

        Args:
            session_id: 会话 ID
            config: 连接配置
            **kwargs: 传递给 Registry.create()

        Raises:
            AdapterSessionStateError: 会话状态不允许连接
        """
        session = self._get_session(session_id)
        if session.state != SessionState.CREATED:
            raise AdapterSessionStateError(
                f"Cannot connect: session is {session.state.value}"
            )
        adapter = self._registry.create(session.adapter_type, **kwargs)
        try:
            adapter.connect(config or {})
            session.transition(SessionState.CONNECTED)
            self._adapters[session_id] = adapter
        except Exception:
            self._adapters.pop(session_id, None)
            raise

    def query(self, session_id: str, query_id: str) -> AdapterQueryResult:
        """
        执行查询。会话必须处于 CONNECTED 状态。

        Args:
            session_id: 会话 ID
            query_id: 查询 ID

        Returns:
            AdapterQueryResult
        """
        session = self._get_session(session_id)
        if session.state != SessionState.CONNECTED:
            raise AdapterSessionStateError(
                f"Cannot query: session is {session.state.value}"
            )
        adapter = self._adapters.get(session_id)
        if adapter is None:
            raise AdapterSessionStateError("No adapter for this session")
        result = adapter.query(query_id)
        return AdapterQueryResult(
            query_id=result.query_id,
            success=result.success,
            data={"stdout": result.stdout, "stderr": result.stderr, "exit_code": result.exit_code},
            message=result.message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def close(self, session_id: str) -> None:
        """
        关闭会话。幂等。释放 adapter。

        已关闭的会话不报错。
        """
        session = self._get_session(session_id)
        if session.is_closed:
            return
        adapter = self._adapters.pop(session_id, None)
        if adapter is not None:
            try:
                adapter.disconnect()
            except Exception:
                pass  # 幂等，忽略关闭错误
        session.transition(SessionState.CLOSED)

    def _get_session(self, session_id: str) -> AdapterSession:
        session = self._sessions.get(session_id)
        if session is None:
            raise AdapterSessionStateError("Unknown session")
        return session

    def get_session(self, session_id: str) -> AdapterSession:
        """获取会话（只读）。"""
        return self._get_session(session_id)
