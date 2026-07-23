"""
WorkOps Adapter Registry — 适配器注册表
Sprint046: Device Adapter Integration Foundation

注册适配器提供者。不允许覆盖、不允许动态加载。
"""

from .adapter_provider import AdapterProvider
from .adapter_errors import AdapterConflictError, AdapterNotFoundError
from ..devices.capability import DeviceCapability


class AdapterIntegrationRegistry:
    """
    适配器注册表。

    不允许覆盖已注册适配器。
    """

    def __init__(self):
        self._providers: dict[str, AdapterProvider] = {}

    def register(self, provider: AdapterProvider) -> None:
        """
        注册适配器提供者。

        Args:
            provider: 适配器提供者

        Raises:
            AdapterConflictError: 重复注册
        """
        if not isinstance(provider, AdapterProvider):
            raise TypeError("provider must be an AdapterProvider instance")
        adapter_id = provider.descriptor().adapter_id
        if adapter_id in self._providers:
            raise AdapterConflictError(adapter_id)
        self._providers[adapter_id] = provider

    def get(self, adapter_id: str) -> AdapterProvider:
        """
        获取适配器提供者。

        Args:
            adapter_id: 适配器 ID

        Returns:
            AdapterProvider

        Raises:
            AdapterNotFoundError: 未注册
        """
        provider = self._providers.get(adapter_id)
        if provider is None:
            raise AdapterNotFoundError(adapter_id)
        return provider

    def list(self) -> list[str]:
        """返回所有已注册适配器 ID。"""
        return list(self._providers.keys())

    def supports(self, capability: DeviceCapability) -> list:
        """
        返回支持某能力的适配器 ID 列表。

        Args:
            capability: 设备能力

        Returns:
            list[str]
        """
        result = []
        for adapter_id, provider in self._providers.items():
            if provider.supports(capability):
                result.append(adapter_id)
        return result
