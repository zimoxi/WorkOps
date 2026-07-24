"""
WorkOps OMV Adapter Provider Contract — OMV 适配器提供者接口
Sprint050: OMV Adapter v1 Foundation

只定义接口。不实现真实连接。
"""

from abc import ABC, abstractmethod

from .v1_model import OMVAdapterDescriptor
from .v1_capability import OMVCapability, OMVOperation


class OMVAdapterProvider(ABC):
    """
    OMV 适配器提供者接口。

    只定义接口。不实现真实连接。
    """

    @abstractmethod
    def descriptor(self) -> OMVAdapterDescriptor:
        """
        返回适配器描述符。

        Returns:
            OMVAdapterDescriptor
        """
        ...

    @abstractmethod
    def supports(self, capability: OMVCapability) -> bool:
        """
        检查是否支持某能力。

        Args:
            capability: OMV 能力

        Returns:
            bool
        """
        ...

    @abstractmethod
    def execute(self, operation: OMVOperation):
        """
        执行操作。

        Args:
            operation: OMV 操作
        """
        ...
