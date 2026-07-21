"""
WorkOps Adapter Capability Provider Contract — 能力提供者契约
Sprint026: Adapter Capability Registry

定义 Adapter 必须声明的能力接口。
不实现连接逻辑。
"""

from abc import ABC, abstractmethod


class AdapterCapabilityProvider(ABC):
    """
    Adapter 能力提供者契约。

    Adapter 必须声明：
    - adapter_type: str
    - supported capabilities: tuple
    """

    @property
    @abstractmethod
    def adapter_type(self) -> str:
        """Adapter 类型标识。"""
        ...

    @property
    @abstractmethod
    def supported_capabilities(self) -> tuple:
        """支持的能力元组。"""
        ...
