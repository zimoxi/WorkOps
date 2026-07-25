"""
WorkOps API Errors — API 错误
Sprint064: API Service Layer Foundation
"""


class APIError(Exception):
    """API 错误基类"""
    pass


class InvalidAPIRequestError(APIError):
    """无效 API 请求"""
    pass


class APIServiceUnavailableError(APIError):
    """API 服务不可用"""
    pass


class APIResponseError(APIError):
    """API 响应错误"""
    pass
