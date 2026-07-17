"""
WorkOps Secret Value — 安全包装
Sprint021: Credential and Secret Management

reveal() 显式读取
str/repr 始终为 [REDACTED]
不允许序列化原文
不在异常中包含原文
"""

from .errors import CredentialValidationError


class SecretValue:
    """Secret Value 安全包装"""

    __slots__ = ('_secret',)

    def __init__(self, secret: str):
        if not isinstance(secret, str):
            raise CredentialValidationError("Secret must be a string")
        if not secret:
            raise CredentialValidationError("Secret cannot be empty")
        self._secret = secret

    def reveal(self) -> str:
        """显式读取"""
        return self._secret

    def __str__(self) -> str:
        return "[REDACTED]"

    def __repr__(self) -> str:
        return "SecretValue([REDACTED])"

    def __format__(self, format_spec: str) -> str:
        """格式化字符串始终返回 [REDACTED]"""
        return "[REDACTED]"

    def __eq__(self, other) -> bool:
        if isinstance(other, SecretValue):
            return self._secret == other._secret
        return False

    def __hash__(self) -> bool:
        return hash(self._secret)
