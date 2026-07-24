"""
WorkOps PVE Adapter v1 Errors — PVE 适配器错误
Sprint049: PVE Adapter v1 Foundation
"""


class PVEAdapterV1Error(Exception):
    """PVE 适配器错误基类"""
    pass


class InvalidPVEAdapterError(PVEAdapterV1Error):
    """无效 PVE 适配器"""
    pass


class PVECapabilityError(PVEAdapterV1Error):
    """PVE 能力错误"""
    pass


class PVEOperationError(PVEAdapterV1Error):
    """PVE 操作错误"""
    pass
