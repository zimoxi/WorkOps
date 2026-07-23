"""
WorkOps Adapter Provider Contract — 适配器提供者接口
Sprint046: Device Adapter Integration Foundation

只定义接口。不实现真实连接。
"""

from abc import ABC, abstractmethod

from .adapter_descriptor import AdapterDescriptor
from ..devices.capability import DeviceCapability


class AdapterProvider(ABC):
    """
    适配器提供者接口。

    只定义接口。不实现真实连接。
    """

    @abstractmethod
    def descriptor(self) -> AdapterDescriptor:
        """
        返回适配器描述符。

        Returns:
            AdapterDescriptor
        """
        ...

    @abstractmethod
    def supports(self, capability: DeviceCapability) -> bool:
        """
        检查是否支持某能力。

        Args:
            capability: 设备能力

        Returns:
            bool
        """
        ...
