"""
WorkOps Role Model — 角色模型
Sprint072: Authentication RBAC Foundation

RoleType enum, Role frozen dataclass
"""

from dataclasses import dataclass
from enum import Enum

from .errors import InvalidIdentityError


class RoleType(Enum):
    """角色类型。"""

    ADMIN = "admin"
    OPERATOR = "operator"
    VIEWER = "viewer"


@dataclass(frozen=True, slots=True)
class Role:
    """
    角色。不可变。
    """

    role_id: str
    role_type: RoleType

    def __post_init__(self):
        if not isinstance(self.role_id, str) or not self.role_id.strip():
            raise InvalidIdentityError("role_id must be a non-empty string")
        if not isinstance(self.role_type, RoleType):
            raise InvalidIdentityError("role_type must be a RoleType instance")
