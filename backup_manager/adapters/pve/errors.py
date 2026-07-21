"""
WorkOps PVE Adapter Errors — PVE 错误模型
Sprint027: PVE ReadOnly Adapter
"""


class PVEAdapterError(Exception):
    """PVE Adapter 错误基类"""
    pass


class PVEQueryError(PVEAdapterError):
    """PVE 查询错误"""
    pass


class PVEUnsupportedOperationError(PVEAdapterError):
    """PVE 不支持的操作"""
    def __init__(self, operation: str = "unknown"):
        super().__init__(f"PVE operation not supported: {operation}")
