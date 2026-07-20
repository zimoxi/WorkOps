"""
WorkOps Capability Matcher — 能力匹配器
Sprint024: Device Capability Model

CapabilityRequirement 描述需求。
CapabilityMatcher.matches() 检查设备是否满足需求。
"""

from dataclasses import dataclass

from .capability import DeviceCapability
from .errors import CapabilityRequirementError
from .model import DeviceModel


@dataclass(frozen=True, slots=True)
class CapabilityRequirement:
    """
    能力需求。不可变。

    required: 必须具备的能力
    optional: 可选能力（不满足不影响匹配结果）
    """

    required: tuple  # tuple[DeviceCapability, ...]
    optional: tuple = ()  # tuple[DeviceCapability, ...]

    def __post_init__(self):
        if not isinstance(self.required, tuple):
            raise CapabilityRequirementError("required must be a tuple")
        for cap in self.required:
            if not isinstance(cap, DeviceCapability):
                raise CapabilityRequirementError(
                    "All required capabilities must be DeviceCapability instances"
                )
        if not isinstance(self.optional, tuple):
            raise CapabilityRequirementError("optional must be a tuple")
        for cap in self.optional:
            if not isinstance(cap, DeviceCapability):
                raise CapabilityRequirementError(
                    "All optional capabilities must be DeviceCapability instances"
                )


class CapabilityMatcher:
    """能力匹配器。检查设备是否满足能力需求。"""

    @staticmethod
    def matches(device: DeviceModel, requirement: CapabilityRequirement) -> bool:
        """
        检查设备是否满足能力需求。

        规则：
        - required 中任一能力缺失 → False
        - optional 缺失 → 不影响结果

        Args:
            device: 设备模型
            requirement: 能力需求

        Returns:
            bool: 是否满足
        """
        device_caps = set(device.capabilities)
        for cap in requirement.required:
            if cap not in device_caps:
                return False
        return True
