"""
WorkOps Security Model — 安全模型
Sprint057: Runtime Security Hardening Foundation

SecurityLevel, SecurityContext
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidSecurityContextError


class SecurityLevel(Enum):
    """安全级别。"""

    STANDARD = "standard"
    RESTRICTED = "restricted"
    PRIVILEGED = "privileged"


@dataclass(frozen=True, slots=True)
class SecurityContext:
    """
    安全上下文。不可变。
    """

    execution_id: str
    level: SecurityLevel
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.execution_id, str) or not self.execution_id.strip():
            raise InvalidSecurityContextError("execution_id must be a non-empty string")
        if not isinstance(self.level, SecurityLevel):
            raise InvalidSecurityContextError("level must be a SecurityLevel instance")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
