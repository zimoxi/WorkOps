"""
WorkOps Adapter Integration Errors — 适配器集成错误
Sprint046: Device Adapter Integration Foundation
"""


class AdapterIntegrationError(Exception):
    """适配器集成错误基类"""
    pass


class InvalidAdapterError(AdapterIntegrationError):
    """无效适配器"""
    pass


class AdapterConflictError(AdapterIntegrationError):
    """适配器冲突"""
    def __init__(self, adapter_id: str):
        super().__init__(f"Adapter already registered: {adapter_id}")


class AdapterNotFoundError(AdapterIntegrationError):
    """适配器未找到"""
    def __init__(self, adapter_id: str):
        super().__init__(f"Adapter not found: {adapter_id}")
