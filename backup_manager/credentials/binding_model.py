"""
WorkOps Credential Binding Model — 凭证绑定模型
Sprint047: Credential Binding Layer Foundation

CredentialType, CredentialReference — frozen dataclass。
"""

from dataclasses import dataclass
from enum import Enum

from .binding_errors import InvalidCredentialReferenceError


class CredentialType(Enum):
    """凭证类型。"""

    SSH = "ssh"
    API_TOKEN = "api_token"
    PASSWORD = "password"


@dataclass(frozen=True, slots=True)
class CredentialReference:
    """
    凭证引用。不可变。

    只标识凭证，不包含凭证值。
    """

    credential_id: str
    credential_type: CredentialType
    provider: str

    def __post_init__(self):
        if not isinstance(self.credential_id, str) or not self.credential_id.strip():
            raise InvalidCredentialReferenceError("credential_id must be a non-empty string")
        if not isinstance(self.credential_type, CredentialType):
            raise InvalidCredentialReferenceError("credential_type must be a CredentialType instance")
        if not isinstance(self.provider, str) or not self.provider.strip():
            raise InvalidCredentialReferenceError("provider must be a non-empty string")
