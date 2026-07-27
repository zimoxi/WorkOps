"""
WorkOps Auth Domain — 认证/授权域
Sprint072: Authentication RBAC Foundation
"""

from .errors import (
    AuthError,
    AuthenticationFailedError,
    AuthorizationDeniedError,
    InvalidIdentityError,
)
from .identity import Identity
from .role import RoleType, Role
from .permission import PermissionType, Permission
from .authentication import AuthenticationProvider
from .authorization import AuthorizationGuard, AuthorizationResult

__all__ = [
    "AuthError",
    "AuthenticationFailedError",
    "AuthorizationDeniedError",
    "InvalidIdentityError",
    "Identity",
    "RoleType",
    "Role",
    "PermissionType",
    "Permission",
    "AuthenticationProvider",
    "AuthorizationGuard",
    "AuthorizationResult",
]
