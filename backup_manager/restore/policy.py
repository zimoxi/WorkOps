"""
WorkOps Restore Policy — 恢复策略
Sprint036: Restore Workflow Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from enum import Enum

from .errors import InvalidRestorePolicyError


class OverwriteMode(Enum):
    """覆盖模式。"""

    NEVER = "never"
    ALWAYS = "always"
    NEWER = "newer"


@dataclass(frozen=True, slots=True)
class RestorePolicy:
    """
    恢复策略。不可变。
    """

    policy_id: str
    overwrite_mode: OverwriteMode = OverwriteMode.NEVER
    verification_required: bool = True

    def __post_init__(self):
        if not isinstance(self.policy_id, str) or not self.policy_id.strip():
            raise InvalidRestorePolicyError("policy_id must be a non-empty string")
        if not isinstance(self.overwrite_mode, OverwriteMode):
            raise InvalidRestorePolicyError("overwrite_mode must be an OverwriteMode instance")
        if not isinstance(self.verification_required, bool):
            raise InvalidRestorePolicyError("verification_required must be a bool")
