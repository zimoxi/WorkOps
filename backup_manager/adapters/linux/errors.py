"""
WorkOps Linux Adapter Errors — Linux 适配器错误
Sprint048: Linux Adapter v1 Foundation
"""


class LinuxAdapterError(Exception):
    """Linux 适配器错误基类"""
    pass


class InvalidLinuxAdapterError(LinuxAdapterError):
    """无效 Linux 适配器"""
    pass


class LinuxCapabilityError(LinuxAdapterError):
    """Linux 能力错误"""
    pass


class LinuxOperationError(LinuxAdapterError):
    """Linux 操作错误"""
    pass
