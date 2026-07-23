"""
WorkOps Credential Requirement — 凭证需求模型
Sprint047: Credential Binding Layer Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .binding_model import CredentialType
from .binding_errors import InvalidCredentialReferenceError


@dataclass(frozen=True, slots=True)
class CredentialRequirement:
    """
    凭证需求。不可变。

    描述适配器需要什么类型的凭证。
    """

    adapter_id: str
    credential_type: CredentialType
    required: bool = True

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidCredentialReferenceError("adapter_id must be a non-empty string")
        if not isinstance(self.credential_type, CredentialType):
            raise InvalidCredentialReferenceError("credential_type must be a CredentialType instance")
        if not isinstance(self.required, bool):
            raise InvalidCredentialReferenceError("required must be a bool")
