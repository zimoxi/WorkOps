"""
WorkOps Credentials Module
Sprint021: Credential and Secret Management
"""

from .errors import (
    CredentialError,
    CredentialValidationError,
    SecretNotFoundError,
    SecretProviderError,
)
from .model import CredentialType, CredentialMetadata
from .secret_value import SecretValue
from .provider import SecretProvider
from .in_memory import InMemorySecretProvider
from .redaction import redact, redact_text

__all__ = [
    "CredentialError",
    "CredentialValidationError",
    "SecretNotFoundError",
    "SecretProviderError",
    "CredentialType",
    "CredentialMetadata",
    "SecretValue",
    "SecretProvider",
    "InMemorySecretProvider",
    "redact",
    "redact_text",
]
