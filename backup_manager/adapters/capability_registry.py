"""
WorkOps Adapter Capability Registry — 能力注册表
Sprint026: Adapter Capability Registry

注册 Adapter 能力声明。
不允许覆盖、不允许动态加载。
"""

from .capability import AdapterCapabilityDeclaration
from ..devices.capability import DeviceCapability
from .errors import (
    AdapterCapabilityError,
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
    CapabilityNotSupportedError,
)


class AdapterCapabilityRegistry:
    """
    Adapter 能力注册表。

    管理 AdapterCapabilityDeclaration。
    不允许覆盖已注册类型。
    """

    def __init__(self):
        self._declarations: dict[str, AdapterCapabilityDeclaration] = {}

    def register(self, declaration: AdapterCapabilityDeclaration) -> None:
        """
        注册 Adapter 能力声明。

        Args:
            declaration: 能力声明

        Raises:
            AdapterAlreadyExistsError: 重复注册
        """
        if not isinstance(declaration, AdapterCapabilityDeclaration):
            raise TypeError("declaration must be an AdapterCapabilityDeclaration")
        key = declaration.adapter_type
        if key in self._declarations:
            raise AdapterAlreadyExistsError(key)
        self._declarations[key] = declaration

    def get(self, adapter_type: str) -> AdapterCapabilityDeclaration:
        """
        获取 Adapter 能力声明。

        Args:
            adapter_type: Adapter 类型

        Returns:
            AdapterCapabilityDeclaration

        Raises:
            AdapterNotFoundError: 未注册
        """
        decl = self._declarations.get(adapter_type)
        if decl is None:
            raise AdapterNotFoundError(adapter_type)
        return decl

    def list(self) -> list[str]:
        """返回所有已注册 adapter_type。"""
        return list(self._declarations.keys())

    def supports(self, adapter_type: str, capability: DeviceCapability) -> bool:
        """
        检查 Adapter 是否支持某能力。

        Args:
            adapter_type: Adapter 类型
            capability: 设备能力

        Returns:
            bool
        """
        decl = self._declarations.get(adapter_type)
        if decl is None:
            return False
        return capability in decl.capabilities
