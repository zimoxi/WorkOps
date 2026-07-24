"""
WorkOps OMV Adapter v1 Errors — OMV 适配器错误
Sprint050: OMV Adapter v1 Foundation
"""


class OMVAdapterV1Error(Exception):
    """OMV 适配器错误基类"""
    pass


class InvalidOMVAdapterError(OMVAdapterV1Error):
    """无效 OMV 适配器"""
    pass


class OMVCapabilityError(OMVAdapterV1Error):
    """OMV 能力错误"""
    pass


class OMVOperationError(OMVAdapterV1Error):
    """OMV 操作错误"""
    pass
