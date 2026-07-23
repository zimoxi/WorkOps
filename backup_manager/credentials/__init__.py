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

# Sprint047: Credential Binding Layer Foundation
from .binding_errors import (
    CredentialBindingError,
    InvalidCredentialReferenceError,
    CredentialBindingConflictError,
    CredentialNotFoundError,
)
from .binding_model import CredentialType, CredentialReference
from .binding_requirement import CredentialRequirement
from .binding import CredentialBinding, CredentialBindingResolver

__all__ += [
    "CredentialBindingError",
    "InvalidCredentialReferenceError",
    "CredentialBindingConflictError",
    "CredentialNotFoundError",
    "CredentialType",
    "CredentialReference",
    "CredentialRequirement",
    "CredentialBinding",
    "CredentialBindingResolver",
]
