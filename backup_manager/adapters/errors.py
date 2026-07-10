"""
WorkOps Adapter Errors — 异常定义
Sprint017: Device Adapter Foundation
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
