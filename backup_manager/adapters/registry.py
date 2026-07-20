"""
WorkOps Adapter Registry — Adapter 注册表
Sprint023: Adapter Runtime Integration Foundation

单例注册表。register() 注册 Descriptor，create() 创建实例。
"""

from .descriptor import AdapterDescriptor
from .errors import AdapterDuplicateError, AdapterNotRegisteredError


class AdapterRegistry:
    """Adapter 注册表。管理 Descriptor 和 Adapter 类型映射。"""

    def __init__(self):
        self._descriptors: dict[str, AdapterDescriptor] = {}
        self._factories: dict[str, type] = {}

    def register(self, descriptor: AdapterDescriptor, adapter_class: type) -> None:
        """
        注册 Adapter 类型。

        Args:
            descriptor: Adapter 描述符
            adapter_class: Adapter 类

        Raises:
            AdapterDuplicateError: 重复注册同类型
        """
        if not isinstance(descriptor, AdapterDescriptor):
            raise TypeError("descriptor must be an AdapterDescriptor")
        if descriptor.adapter_type in self._descriptors:
            raise AdapterDuplicateError(descriptor.adapter_type)
        self._descriptors[descriptor.adapter_type] = descriptor
        self._factories[descriptor.adapter_type] = adapter_class

    def get_descriptor(self, adapter_type: str) -> AdapterDescriptor:
        """
        获取 Adapter 描述符。

        Args:
            adapter_type: Adapter 类型

        Returns:
            AdapterDescriptor

        Raises:
            AdapterNotRegisteredError: 类型未注册
        """
        desc = self._descriptors.get(adapter_type)
        if desc is None:
            raise AdapterNotRegisteredError(adapter_type)
        return desc

    def create(self, adapter_type: str, **kwargs):
        """
        创建 Adapter 实例。

        Args:
            adapter_type: Adapter 类型
            **kwargs: 传递给 Adapter 构造函数

        Returns:
            BaseAdapter 实例

        Raises:
            AdapterNotRegisteredError: 类型未注册
        """
        if adapter_type not in self._descriptors:
            raise AdapterNotRegisteredError(adapter_type)
        factory = self._factories[adapter_type]
        return factory(**kwargs)

    def list_types(self) -> list[str]:
        """返回所有已注册类型。"""
        return list(self._descriptors.keys())

    def is_registered(self, adapter_type: str) -> bool:
        """检查类型是否已注册。"""
        return adapter_type in self._descriptors
