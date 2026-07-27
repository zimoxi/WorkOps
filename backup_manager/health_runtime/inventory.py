"""
WorkOps Runtime Inventory — 运行时设备清单
Sprint076: Runtime Health Probe and Device Inventory

Defines device inventory boundary.
"""

from abc import ABC, abstractmethod


class RuntimeInventory(ABC):
    """
    运行时设备清单接口。

    返回: tuple[RuntimeDevice, ...]
    """

    @abstractmethod
    def list_devices(self) -> tuple:
        """
        列出所有设备。

        Returns:
            tuple[RuntimeDevice, ...]
        """
        ...
