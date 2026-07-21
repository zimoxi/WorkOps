"""
WorkOps Device Inventory Repository — 设备清单仓库
Sprint025: Device Inventory

内存实现。不使用数据库。
"""

from .inventory import DeviceRecord
from .errors import DeviceAlreadyExistsError, DeviceNotFoundError


class DeviceInventoryRepository:
    """
    设备清单仓库。内存实现。

    不使用数据库，为未来持久化层预留接口。
    """

    def __init__(self):
        self._devices: dict[str, DeviceRecord] = {}

    def add(self, device: DeviceRecord) -> None:
        """
        添加设备。

        Args:
            device: 设备记录

        Raises:
            DeviceAlreadyExistsError: 设备已存在
        """
        if not isinstance(device, DeviceRecord):
            raise TypeError("device must be a DeviceRecord")
        if device.device_id in self._devices:
            raise DeviceAlreadyExistsError(device.device_id)
        self._devices[device.device_id] = device

    def get(self, device_id: str) -> DeviceRecord:
        """
        获取设备。

        Args:
            device_id: 设备 ID

        Returns:
            DeviceRecord

        Raises:
            DeviceNotFoundError: 设备不存在
        """
        device = self._devices.get(device_id)
        if device is None:
            raise DeviceNotFoundError(device_id)
        return device

    def list(self) -> list[DeviceRecord]:
        """返回所有设备。"""
        return list(self._devices.values())

    def remove(self, device_id: str) -> None:
        """
        删除设备。

        Args:
            device_id: 设备 ID

        Raises:
            DeviceNotFoundError: 设备不存在
        """
        if device_id not in self._devices:
            raise DeviceNotFoundError(device_id)
        del self._devices[device_id]

    def count(self) -> int:
        """返回设备数量。"""
        return len(self._devices)
