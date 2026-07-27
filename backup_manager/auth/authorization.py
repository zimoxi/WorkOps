"""
WorkOps Authorization — 授权守卫和结果
Sprint072: Authentication RBAC Foundation

AuthorizationResult, AuthorizationGuard
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from abc import ABC, abstractmethod

from .identity import Identity
from .permission import Permission
from .errors import InvalidIdentityError


@dataclass(frozen=True, slots=True)
class AuthorizationResult:
    """
    授权结果。不可变。
    """

    allowed: bool
    reason: str
    checked_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.allowed, bool):
            raise InvalidIdentityError("allowed must be a bool")
        if not isinstance(self.reason, str):
            raise InvalidIdentityError("reason must be a string")
        if self.checked_at is None:
            object.__setattr__(self, "checked_at", datetime.now(timezone.utc))


class AuthorizationGuard(ABC):
    """
    授权守卫接口。

    定义访问决策边界。
    """

    @abstractmethod
    def authorize(self, identity: Identity, permission: Permission) -> AuthorizationResult:
        """
        授权检查。

        Args:
            identity: 用户身份
            permission: 请求的权限

        Returns:
            AuthorizationResult
        """
        ...
