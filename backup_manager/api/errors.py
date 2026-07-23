"""
WorkOps Operation API Errors — 操作 API 错误
Sprint045: Unified Operation API Foundation
"""


class OperationAPIError(Exception):
    """操作 API 错误基类"""
    pass


class InvalidOperationRequestError(OperationAPIError):
    """无效操作请求"""
    pass


class OperationSubmissionError(OperationAPIError):
    """操作提交失败"""
    pass


class OperationUnavailableError(OperationAPIError):
    """操作不可用"""
    pass
