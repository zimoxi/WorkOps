"""
WorkOps Device Capability Registry — 设备能力注册表
Sprint024: Device Capability Model

注册设备类型和能力映射。
不允许动态加载、不允许覆盖。
"""

from .capability import DeviceCapability, DeviceType
from .errors import CapabilityConflictError, CapabilityNotFoundError


class DeviceCapabilityRegistry:
    """
    设备能力注册表。

    注册设备类型和能力映射。
    不允许覆盖已注册类型。
    """

    def __init__(self):
        self._registry: dict[str, tuple] = {}  # device_type.value -> tuple[DeviceCapability]

    def register(self, device_type: DeviceType, capabilities: tuple) -> None:
        """
        注册设备类型能力。

        Args:
            device_type: 设备类型
            capabilities: 能力元组

        Raises:
            CapabilityConflictError: 重复注册
        """
        if not isinstance(device_type, DeviceType):
            raise TypeError("device_type must be a DeviceType instance")
        if not isinstance(capabilities, tuple):
            raise TypeError("capabilities must be a tuple")
        for cap in capabilities:
            if not isinstance(cap, DeviceCapability):
                raise TypeError("All capabilities must be DeviceCapability instances")
        key = device_type.value
        if key in self._registry:
            raise CapabilityConflictError(
                f"Device type already registered: {device_type.name}"
            )
        self._registry[key] = capabilities

    def get(self, device_type: DeviceType) -> tuple:
        """
        获取设备类型能力。

        Args:
            device_type: 设备类型

        Returns:
            tuple[DeviceCapability]

        Raises:
            CapabilityNotFoundError: 未注册
        """
        key = device_type.value
        caps = self._registry.get(key)
        if caps is None:
            raise CapabilityNotFoundError(
                f"Device type not registered: {device_type.name}"
            )
        return caps

    def list(self) -> dict:
        """返回所有已注册类型和能力。"""
        return dict(self._registry)

    def supports(self, device_type: DeviceType, capability: DeviceCapability) -> bool:
        """
        检查设备类型是否支持某能力。

        Args:
            device_type: 设备类型
            capability: 设备能力

        Returns:
            bool
        """
        key = device_type.value
        caps = self._registry.get(key)
        if caps is None:
            return False
        return capability in caps
