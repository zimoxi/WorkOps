"""
WorkOps Device Service — 设备服务
Sprint077: Device Management Foundation

Application boundary for devices.
"""

from abc import ABC, abstractmethod


class DeviceService(ABC):
    """
    设备服务接口。

    应用层设备边界。
    """

    @abstractmethod
    def register_device(self, device) -> None:
        """
        注册设备。

        Args:
            device: Device instance
        """
        ...

    @abstractmethod
    def list_devices(self) -> tuple:
        """
        列出所有设备。

        Returns:
            tuple[Device, ...]
        """
        ...

    @abstractmethod
    def get_device(self, device_id: str):
        """
        获取设备。

        Args:
            device_id: 设备 ID

        Returns:
            Device or None
        """
        ...
