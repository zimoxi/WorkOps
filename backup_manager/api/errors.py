"""
WorkOps API Errors — 错误定义
Sprint014: API Layer Foundation

错误码和异常类定义
Sprint014 只定义，不执行权限判断
"""


class ApiError(Exception):
    """API 错误基类"""

    def __init__(self, code, message, status_code=400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(ApiError):
    """400 请求参数错误"""

    def __init__(self, message="Validation failed", details=None):
        super().__init__("VALIDATION_ERROR", message, 400)
        self.details = details


class UnauthorizedError(ApiError):
    """401 未认证"""

    def __init__(self, message="Authentication required"):
        super().__init__("UNAUTHORIZED", message, 401)


class ForbiddenError(ApiError):
    """403 无权限（只定义，Sprint014 不使用）"""

    def __init__(self, message="Permission denied"):
        super().__init__("FORBIDDEN", message, 403)


class NotFoundError(ApiError):
    """404 资源不存在"""

    def __init__(self, resource="Resource"):
        super().__init__("NOT_FOUND", f"{resource} not found", 404)


class ConflictError(ApiError):
    """409 资源冲突"""

    def __init__(self, message="Resource conflict"):
        super().__init__("CONFLICT", message, 409)


class InternalError(ApiError):
    """500 服务器内部错误"""

    def __init__(self, message="Internal server error"):
        super().__init__("INTERNAL_ERROR", message, 500)
