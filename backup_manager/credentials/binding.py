"""
WorkOps Credential Binding — 凭证绑定和解析器
Sprint047: Credential Binding Layer Foundation

CredentialBinding frozen dataclass。
CredentialBindingResolver ABC。
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod

from .binding_model import CredentialReference
from .binding_errors import InvalidCredentialReferenceError


@dataclass(frozen=True, slots=True)
class CredentialBinding:
    """
    凭证绑定。不可变。

    绑定适配器身份和凭证引用。
    不包含凭证值。
    """

    adapter_id: str
    reference: CredentialReference

    def __post_init__(self):
        if not isinstance(self.adapter_id, str) or not self.adapter_id.strip():
            raise InvalidCredentialReferenceError("adapter_id must be a non-empty string")
        if not isinstance(self.reference, CredentialReference):
            raise InvalidCredentialReferenceError("reference must be a CredentialReference instance")


class CredentialBindingResolver(ABC):
    """
    凭证绑定解析器接口。

    只定义接口。不实现真实解析。
    """

    @abstractmethod
    def resolve(self, adapter_id: str) -> CredentialReference:
        """
        解析适配器的凭证引用。

        Args:
            adapter_id: 适配器 ID

        Returns:
            CredentialReference
        """
        ...
