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


class InvalidDeviceError(DeviceError):
    """无效设备"""
    pass


class CapabilityNotFoundError(DeviceError):
    """能力未找到"""
    pass


class CapabilityConflictError(DeviceError):
    """能力冲突（重复注册）"""
    pass


class DeviceInventoryError(DeviceError):
    """设备清单错误"""
    pass


class DeviceAlreadyExistsError(DeviceInventoryError):
    """设备已存在"""
    def __init__(self, device_id: str):
        super().__init__(f"Device already exists: {device_id}")


class DeviceNotFoundError(DeviceInventoryError):
    """设备未找到"""
    def __init__(self, device_id: str):
        super().__init__(f"Device not found: {device_id}")
