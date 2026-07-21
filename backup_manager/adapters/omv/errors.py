"""
WorkOps OMV Adapter Errors — OMV 错误模型
Sprint028: OMV ReadOnly Adapter
"""


class OMVAdapterError(Exception):
    """OMV Adapter 错误基类"""
    pass


class OMVQueryError(OMVAdapterError):
    """OMV 查询错误"""
    pass


class OMVUnsupportedOperationError(OMVAdapterError):
    """OMV 不支持的操作"""
    def __init__(self, operation: str = "unknown"):
        super().__init__(f"OMV operation not supported: {operation}")
