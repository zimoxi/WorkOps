"""
WorkOps Release Errors — 发布错误
Sprint065: Release Candidate Foundation
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
