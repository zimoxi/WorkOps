"""
WorkOps Security Policy — 安全策略
Sprint057: Runtime Security Hardening Foundation

RuntimePermission, CredentialAccessPolicy
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidSecurityContextError


class RuntimePermission(Enum):
    """运行时权限。"""

    READ = "read"
    EXECUTE = "execute"
    MODIFY = "modify"


@dataclass(frozen=True, slots=True)
class CredentialAccessPolicy:
    """
    凭证访问策略。不可变。

    只控制权限。不包含凭证值。
    """

    adapter_id: str
    allowed: bool
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidSecurityContextError("adapter_id must be a non-empty string")
        if not isinstance(self.allowed, bool):
            raise InvalidSecurityContextError("allowed must be a bool")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
