"""
WorkOps Credential Errors — 错误定义
Sprint021: Credential and Secret Management

异常消息不得包含 Secret Value 或 secret_ref 原文。
"""


class CredentialError(Exception):
    """Credential 错误基类"""
    pass


class CredentialValidationError(CredentialError):
    """输入校验错误"""
    pass


class SecretNotFoundError(CredentialError):
    """Secret 不存在"""
    pass


class SecretProviderError(CredentialError):
    """SecretProvider 错误"""
    pass
