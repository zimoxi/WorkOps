"""
WorkOps Adapter Errors — 异常定义
Sprint017: Device Adapter Foundation
Sprint023: 新增 Runtime 错误类
"""


class AdapterError(Exception):
    """Adapter 错误基类"""
    pass


class AdapterNotConnectedError(AdapterError):
    """设备未连接"""
    def __init__(self, message="Device not connected"):
        super().__init__(message)


class AdapterNotImplementedError(AdapterError):
    """Adapter 未实现"""
    def __init__(self, adapter_type="Adapter"):
        super().__init__(f"{adapter_type} not implemented")


class AdapterExecutionError(AdapterError):
    """命令执行失败"""
    def __init__(self, message="Command execution failed"):
        super().__init__(message)


class AdapterDescriptorError(AdapterError):
    """Adapter 描述符错误"""
    pass


class AdapterDuplicateError(AdapterError):
    """重复注册 Adapter 类型"""
    def __init__(self, adapter_type: str):
        super().__init__(f"Adapter type already registered: {adapter_type}")


class AdapterNotRegisteredError(AdapterError):
    """Adapter 类型未注册"""
    def __init__(self, adapter_type: str):
        super().__init__(f"Adapter type not registered: {adapter_type}")


class AdapterSessionStateError(AdapterError):
    """会话状态错误"""
    pass
