"""
WorkOps Device Management Errors — 设备管理错误
Sprint077: Device Management Foundation
"""


class DeviceError(Exception):
    """设备错误基类"""
    pass


class DeviceManagementError(DeviceError):
    """设备管理错误"""
    pass


class DeviceNotFoundError(DeviceManagementError):
    """设备未找到"""
    pass


class InvalidDeviceError(DeviceManagementError):
    """无效设备"""
    pass


class DeviceTypeError(DeviceError):
    """设备类型错误"""
    pass


class DeviceCapabilityError(DeviceError):
    """设备能力错误"""
    pass


class DeviceModelValidationError(DeviceError):
    """设备模型验证错误"""
    pass


class CapabilityRequirementError(DeviceError):
    """能力需求错误"""
    pass


class CapabilityConflictError(DeviceError):
    """能力冲突"""
    pass


class CapabilityNotFoundError(DeviceError):
    """能力未找到"""
    pass


class DeviceInventoryError(DeviceError):
    """设备清单错误"""
    pass


class DeviceAlreadyExistsError(DeviceError):
    """设备已存在"""
    pass
