"""
WorkOps Identity Model — 身份模型
Sprint072: Authentication RBAC Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidIdentityError


@dataclass(frozen=True, slots=True)
class Identity:
    """
    用户身份。不可变。
    """

    identity_id: str
    username: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.identity_id, str) or not self.identity_id.strip():
            raise InvalidIdentityError("identity_id must be a non-empty string")
        if not isinstance(self.username, str) or not self.username.strip():
            raise InvalidIdentityError("username must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
