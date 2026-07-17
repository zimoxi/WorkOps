"""
WorkOps Credential Model — 凭据模型
Sprint021: Credential and Secret Management

字段严格为：
- credential_id
- name
- credential_type
- username
- secret_ref
- created_at
- updated_at
- disabled_at

不包含 Secret Value。
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .errors import CredentialValidationError


class CredentialType(Enum):
    """凭据类型"""
    PASSWORD = "password"
    PRIVATE_KEY = "private_key"
    TOKEN = "token"


@dataclass(frozen=True, slots=True)
class CredentialMetadata:
    """凭据元数据（不可变）"""
    credential_id: str
    name: str
    credential_type: CredentialType
    username: str
    secret_ref: str
    created_at: datetime
    updated_at: datetime
    disabled_at: Optional[datetime] = None

    def __post_init__(self):
        # 校验 credential_id
        if not isinstance(self.credential_id, str) or not self.credential_id.strip():
            raise CredentialValidationError("credential_id must be a non-empty string")

        # 校验 name
        if not isinstance(self.name, str) or not self.name.strip():
            raise CredentialValidationError("name must be a non-empty string")

        # 校验 credential_type
        if not isinstance(self.credential_type, CredentialType):
            raise CredentialValidationError("credential_type must be a CredentialType")

        # 校验 username
        if not isinstance(self.username, str):
            raise CredentialValidationError("username must be a string")

        # 校验 secret_ref
        if not isinstance(self.secret_ref, str) or not self.secret_ref.strip():
            raise CredentialValidationError("secret_ref must be a non-empty string")

        # 校验时间字段
        if not isinstance(self.created_at, datetime):
            raise CredentialValidationError("created_at must be a datetime")
        if not isinstance(self.updated_at, datetime):
            raise CredentialValidationError("updated_at must be a datetime")
        if self.disabled_at is not None and not isinstance(self.disabled_at, datetime):
            raise CredentialValidationError("disabled_at must be a datetime or None")

    def __repr__(self) -> str:
        """不显示 secret_ref"""
        return (
            f"CredentialMetadata("
            f"credential_id={self.credential_id!r}, "
            f"name={self.name!r}, "
            f"credential_type={self.credential_type.value!r}, "
            f"username={self.username!r}"
            f")"
        )

    def __str__(self) -> str:
        """不显示 secret_ref"""
        return (
            f"CredentialMetadata("
            f"id={self.credential_id}, "
            f"name={self.name}, "
            f"type={self.credential_type.value}, "
            f"username={self.username}"
            f")"
        )

    def to_safe_dict(self) -> dict:
        """安全字典输出，不返回 secret_ref"""
        return {
            "credential_id": self.credential_id,
            "name": self.name,
            "credential_type": self.credential_type.value,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "disabled_at": self.disabled_at.isoformat() if self.disabled_at else None,
        }
