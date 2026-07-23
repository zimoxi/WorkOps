"""
WorkOps Linux Adapter Provider Contract — Linux 适配器提供者接口
Sprint048: Linux Adapter v1 Foundation

只定义接口。不实现真实连接。
"""

from abc import ABC, abstractmethod

from .model import LinuxAdapterDescriptor
from .capability import LinuxCapability, LinuxOperation


class LinuxAdapterProvider(ABC):
    """
    Linux 适配器提供者接口。

    只定义接口。不实现真实连接。
    """

    @abstractmethod
    def descriptor(self) -> LinuxAdapterDescriptor:
        """
        返回适配器描述符。

        Returns:
            LinuxAdapterDescriptor
        """
        ...

    @abstractmethod
    def supports(self, capability: LinuxCapability) -> bool:
        """
        检查是否支持某能力。

        Args:
            capability: Linux 能力

        Returns:
            bool
        """
        ...

    @abstractmethod
    def execute(self, operation: LinuxOperation):
        """
        执行操作。

        Args:
            operation: Linux 操作
        """
        ...
