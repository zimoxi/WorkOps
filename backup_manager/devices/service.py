"""
WorkOps Device Inventory Service — 设备清单服务
Sprint025: Device Inventory

管理设备注册、状态变更、查询。
不实现连接/执行/扫描/发现。
"""

from datetime import datetime, timezone

from .capability import DeviceCapability, DeviceType
from .inventory import DeviceRecord
from .status import DeviceStatus
from .repository import DeviceInventoryRepository
from .errors import DeviceInventoryError


class DeviceInventoryService:
    """
    设备清单服务。

    职责：register / disable / retire / lookup。
    不实现：connect / execute / scan / discover。
    """

    def __init__(self, repository: DeviceInventoryRepository = None):
        self._repo = repository or DeviceInventoryRepository()

    def register(
        self,
        device_id: str,
        name: str,
        device_type: DeviceType,
        capabilities: tuple,
        adapter_type: str,
    ) -> DeviceRecord:
        """
        注册设备。

        Args:
            device_id: 设备 ID
            name: 设备名称
            device_type: 设备类型
            capabilities: 能力元组
            adapter_type: 适配器类型

        Returns:
            DeviceRecord
        """
        now = datetime.now(timezone.utc)
        record = DeviceRecord(
            device_id=device_id,
            name=name,
            device_type=device_type,
            capabilities=capabilities,
            adapter_type=adapter_type,
            status=DeviceStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        self._repo.add(record)
        return record

    def disable(self, device_id: str) -> DeviceRecord:
        """
        禁用设备。

        Args:
            device_id: 设备 ID

        Returns:
            DeviceRecord (updated)
        """
        device = self._repo.get(device_id)
        now = datetime.now(timezone.utc)
        updated = DeviceRecord(
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
            capabilities=device.capabilities,
            adapter_type=device.adapter_type,
            status=DeviceStatus.DISABLED,
            created_at=device.created_at,
            updated_at=now,
        )
        self._repo.remove(device_id)
        self._repo.add(updated)
        return updated

    def retire(self, device_id: str) -> DeviceRecord:
        """
        退役设备。

        Args:
            device_id: 设备 ID

        Returns:
            DeviceRecord (updated)
        """
        device = self._repo.get(device_id)
        now = datetime.now(timezone.utc)
        updated = DeviceRecord(
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
            capabilities=device.capabilities,
            adapter_type=device.adapter_type,
            status=DeviceStatus.RETIRED,
            created_at=device.created_at,
            updated_at=now,
        )
        self._repo.remove(device_id)
        self._repo.add(updated)
        return updated

    def lookup(self, device_id: str) -> DeviceRecord:
        """
        查询设备。

        Args:
            device_id: 设备 ID

        Returns:
            DeviceRecord
        """
        return self._repo.get(device_id)

    def list_all(self) -> list[DeviceRecord]:
        """返回所有设备。"""
        return self._repo.list()

    @property
    def repository(self) -> DeviceInventoryRepository:
        """返回底层仓库（只读访问）。"""
        return self._repo
