"""
WorkOps Device Errors — 设备域错误
Sprint024: Device Capability Model
"""


class DeviceError(Exception):
    """设备域错误基类"""
    pass


class DeviceTypeError(DeviceError):
    """设备类型错误"""
    pass


class DeviceCapabilityError(DeviceError):
    """设备能力错误"""
    pass


class DeviceModelValidationError(DeviceError):
    """设备模型校验错误"""
    pass


class CapabilityRequirementError(DeviceError):
    """能力需求错误"""
    pass
