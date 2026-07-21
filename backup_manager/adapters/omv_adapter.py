"""
WorkOps OMV Adapter — OMV 只读适配器
Sprint028: OMV ReadOnly Adapter

adapter_type: "omv"
Capabilities: SYSTEM_INFO, STATUS_QUERY, STORAGE_QUERY, BACKUP_TARGET
只读。不实现文件系统修改/SMB/NFS/RAID/用户管理。
"""

from .base import BaseAdapter
from .capability import AdapterCapabilityDeclaration
from .capability_registry import AdapterCapabilityRegistry
from .errors import AdapterNotConnectedError
from ..devices.capability import DeviceCapability
from .omv.errors import OMVAdapterError, OMVUnsupportedOperationError
from .omv.models import OMVSystemInfo, OMVStorageInfo, OMVStatus


# 能力声明
OMV_CAPABILITIES = (
    DeviceCapability.SYSTEM_INFO,
    DeviceCapability.STATUS_QUERY,
    DeviceCapability.STORAGE_QUERY,
    DeviceCapability.BACKUP_TARGET,
)


class OMVAdapter(BaseAdapter):
    """
    OMV 只读适配器。

    只读查询。不实现文件系统修改/SMB/NFS/RAID/用户管理。
    """

    adapter_type = "omv"

    def __init__(self, client=None):
        self._client = client
        self._connected = False

    @classmethod
    def capability_declaration(cls) -> AdapterCapabilityDeclaration:
        """返回能力声明。"""
        return AdapterCapabilityDeclaration(
            adapter_type=cls.adapter_type,
            capabilities=OMV_CAPABILITIES,
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
        raise OMVUnsupportedOperationError("execute")

    def query_status(self) -> dict:
        """查询设备状态。"""
        if not self._connected:
            raise AdapterNotConnectedError("OMV not connected")
        return {"online": True, "adapter": self.adapter_type}

    def query(self, query_id: str):
        """
        查询 OMV 信息。

        只支持预定义的查询类型。
        """
        if not self._connected:
            raise AdapterNotConnectedError("OMV not connected")
        if query_id == "system_info":
            return self._query_system_info()
        elif query_id == "storage":
            return self._query_storage()
        elif query_id == "status":
            return self._query_status()
        else:
            raise OMVUnsupportedOperationError(f"query:{query_id}")

    def _query_system_info(self):
        if self._client is not None:
            return self._client.get_system_info()
        return {}

    def _query_storage(self):
        if self._client is not None:
            return self._client.get_storage()
        return []

    def _query_status(self):
        if self._client is not None:
            return self._client.get_status()
        return {}
