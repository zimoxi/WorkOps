"""
WorkOps Device Registry — 设备注册表
Sprint077: Device Management Foundation

Store device definitions. Retrieve devices. Provide inventory.
No persistence required.
"""

from abc import ABC, abstractmethod


class DeviceRegistry(ABC):
    """
    设备注册表接口。

    职责:
    - 存储设备定义
    - 检索设备
    - 提供清单

    不要求持久化。
    """

    @abstractmethod
    def register(self, device) -> None:
        """
        注册设备。

        Args:
            device: Device instance
        """
        ...

    @abstractmethod
    def get(self, device_id: str):
        """
        获取设备。

        Args:
            device_id: 设备 ID

        Returns:
            Device or None
        """
        ...

    @abstractmethod
    def list_all(self) -> tuple:
        """
        列出所有设备。

        Returns:
            tuple[Device, ...]
        """
        ...
