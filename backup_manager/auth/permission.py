"""
WorkOps Permission Model — 权限模型
Sprint072: Authentication RBAC Foundation

PermissionType enum, Permission frozen dataclass
"""

from dataclasses import dataclass
from enum import Enum

from .errors import InvalidIdentityError


class PermissionType(Enum):
    """权限类型。"""

    READ = "read"
    EXECUTE = "execute"
    BACKUP = "backup"
    RESTORE = "restore"
    ADMIN = "admin"


@dataclass(frozen=True, slots=True)
class Permission:
    """
    权限。不可变。
    """

    permission_id: str
    permission_type: PermissionType

    def __post_init__(self):
        if not isinstance(self.permission_id, str) or not self.permission_id.strip():
            raise InvalidIdentityError("permission_id must be a non-empty string")
        if not isinstance(self.permission_type, PermissionType):
            raise InvalidIdentityError("permission_type must be a PermissionType instance")
