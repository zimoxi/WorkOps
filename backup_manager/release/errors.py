"""
WorkOps Release Errors — 发布错误
Sprint065/Sprint074: Release Candidate Foundation / WorkOps v1.0 Stable Release
"""


class ReleaseError(Exception):
    """发布错误基类"""
    pass


class InvalidReleaseMetadataError(ReleaseError):
    """无效发布元数据"""
    pass


class ReleaseValidationError(ReleaseError):
    """发布验证错误"""
    pass


class ReleaseUnavailableError(ReleaseError):
    """发布不可用"""
    pass


class StableReleaseError(ReleaseError):
    """稳定发布错误"""
    pass


class ReleaseBlockedError(StableReleaseError):
    """发布阻塞"""
    pass


class InvalidReleaseStateError(StableReleaseError):
    """无效发布状态"""
    pass
