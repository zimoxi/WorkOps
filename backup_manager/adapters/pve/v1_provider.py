"""
WorkOps PVE Adapter Provider Contract — PVE 适配器提供者接口
Sprint049: PVE Adapter v1 Foundation

只定义接口。不实现真实连接。
"""

from abc import ABC, abstractmethod

from .v1_model import PVEAdapterDescriptor
from .v1_capability import PVECapability, PVEOperation


class PVEAdapterProvider(ABC):
    """
    PVE 适配器提供者接口。

    只定义接口。不实现真实连接。
    """

    @abstractmethod
    def descriptor(self) -> PVEAdapterDescriptor:
        """
        返回适配器描述符。

        Returns:
            PVEAdapterDescriptor
        """
        ...

    @abstractmethod
    def supports(self, capability: PVECapability) -> bool:
        """
        检查是否支持某能力。

        Args:
            capability: PVE 能力

        Returns:
            bool
        """
        ...

    @abstractmethod
    def execute(self, operation: PVEOperation):
        """
        执行操作。

        Args:
            operation: PVE 操作
        """
        ...
