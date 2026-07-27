"""
WorkOps HTTP API Errors — HTTP API 错误
Sprint066: HTTP API Runtime Foundation
"""


class HTTPAPIError(Exception):
    """HTTP API 错误基类"""
    pass


class InvalidHTTPRequestError(HTTPAPIError):
    """无效 HTTP 请求"""
    pass


class HTTPRouteError(HTTPAPIError):
    """HTTP 路由错误"""
    pass


class HTTPServiceUnavailableError(HTTPAPIError):
    """HTTP 服务不可用"""
    pass
