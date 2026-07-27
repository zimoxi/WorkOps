"""
WorkOps Auth Errors — 认证/授权错误
Sprint072: Authentication RBAC Foundation
"""


class AuthError(Exception):
    """认证/授权错误基类"""
    pass


class AuthenticationFailedError(AuthError):
    """认证失败"""
    pass


class AuthorizationDeniedError(AuthError):
    """授权拒绝"""
    pass


class InvalidIdentityError(AuthError):
    """无效身份"""
    pass
