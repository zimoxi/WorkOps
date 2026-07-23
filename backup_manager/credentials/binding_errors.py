"""
WorkOps Credential Binding Errors — 凭证绑定错误
Sprint047: Credential Binding Layer Foundation
"""


class CredentialBindingError(Exception):
    """凭证绑定错误基类"""
    pass


class InvalidCredentialReferenceError(CredentialBindingError):
    """无效凭证引用"""
    pass


class CredentialBindingConflictError(CredentialBindingError):
    """凭证绑定冲突"""
    def __init__(self, adapter_id: str):
        super().__init__(f"Credential binding already exists: {adapter_id}")


class CredentialNotFoundError(CredentialBindingError):
    """凭证未找到"""
    def __init__(self, credential_id: str):
        super().__init__(f"Credential not found: {credential_id}")
