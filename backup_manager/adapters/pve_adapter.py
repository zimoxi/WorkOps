"""
WorkOps PVE Adapter — PVE 只读适配器
Sprint027: PVE ReadOnly Adapter

adapter_type: "pve"
Capabilities: SYSTEM_INFO, STATUS_QUERY, STORAGE_QUERY
只读。不实现 VM 创建/删除/修改。
"""

from .base import BaseAdapter
from .capability import AdapterCapabilityDeclaration
from .capability_registry import AdapterCapabilityRegistry
from .errors import AdapterNotConnectedError
from ..devices.capability import DeviceCapability
from .pve.errors import PVEAdapterError, PVEUnsupportedOperationError
from .pve.models import PVENodeInfo, PVEStorageInfo, PVEStatus


# 能力声明
PVE_CAPABILITIES = (
    DeviceCapability.SYSTEM_INFO,
    DeviceCapability.STATUS_QUERY,
    DeviceCapability.STORAGE_QUERY,
)


class PVEAdapter(BaseAdapter):
    """
    PVE 只读适配器。

    只读查询。不实现 VM 创建/删除/修改。
    """

    adapter_type = "pve"

    def __init__(self, client=None):
        self._client = client
        self._connected = False

    @classmethod
    def capability_declaration(cls) -> AdapterCapabilityDeclaration:
        """返回能力声明。"""
        return AdapterCapabilityDeclaration(
            adapter_type=cls.adapter_type,
            capabilities=PVE_CAPABILITIES,
        )

    @classmethod
    def register_to_registry(cls, registry: AdapterCapabilityRegistry) -> None:
        """注册到能力注册表。"""
        registry.register(cls.capability_declaration())

    def connect(self, device: dict) -> bool:
        """连接（Mock）。"""
        self._connected = True
        return True

    def disconnect(self) -> None:
        """断开连接。"""
        self._connected = False

    def execute(self, command: str) -> dict:
        """永久拒绝任意命令。"""
        raise PVEUnsupportedOperationError("execute")

    def query_status(self) -> dict:
        """查询设备状态。"""
        if not self._connected:
            raise AdapterNotConnectedError("PVE not connected")
        return {"online": True, "adapter": self.adapter_type}

    def query(self, query_id: str):
        """
        查询 PVE 信息。

        只支持预定义的查询类型。
        """
        if not self._connected:
            raise AdapterNotConnectedError("PVE not connected")
        if query_id == "nodes":
            return self._query_nodes()
        elif query_id == "storage":
            return self._query_storage()
        elif query_id == "status":
            return self._query_status()
        else:
            raise PVEUnsupportedOperationError(f"query:{query_id}")

    def _query_nodes(self):
        if self._client is not None:
            return self._client.get_nodes()
        return []

    def _query_storage(self):
        if self._client is not None:
            return self._client.get_storage("*")
        return []

    def _query_status(self):
        if self._client is not None:
            return self._client.get_status("*")
        return {}
