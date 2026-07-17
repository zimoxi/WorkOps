"""
WorkOps In-Memory Secret Provider — 测试用内存实现
Sprint021: Credential and Secret Management

使用 secrets 模块生成不可预测引用
单进程内存实现
不承诺线程安全
重启后全部丢失
"""

import secrets

from .errors import CredentialValidationError, SecretNotFoundError
from .provider import SecretProvider
from .secret_value import SecretValue


class InMemorySecretProvider(SecretProvider):
    """In-Memory Secret Provider 实现"""

    def __init__(self):
        self._store = {}  # secret_ref -> str (原始 Secret)

    def store(self, secret_value) -> str:
        """
        存储 Secret，返回 secret_ref
        
        Args:
            secret_value: str 或 SecretValue
        
        Returns:
            secret_ref: 不可预测的引用字符串
        """
        # 处理输入
        if isinstance(secret_value, SecretValue):
            raw_secret = secret_value.reveal()
        elif isinstance(secret_value, str):
            raw_secret = secret_value
        else:
            raise CredentialValidationError("Secret must be str or SecretValue")

        # 校验
        if not raw_secret:
            raise CredentialValidationError("Secret cannot be empty")

        # 生成不可预测引用
        secret_ref = secrets.token_urlsafe(32)

        # 处理极小概率碰撞
        while secret_ref in self._store:
            secret_ref = secrets.token_urlsafe(32)

        # 保存原始字符串（独立副本）
        self._store[secret_ref] = str(raw_secret)

        return secret_ref

    def retrieve(self, secret_ref: str) -> SecretValue:
        """
        获取 Secret
        
        Args:
            secret_ref: Secret 引用
        
        Returns:
            SecretValue（新的包装）
        
        Raises:
            SecretNotFoundError: 引用不存在
        """
        # 校验
        if not isinstance(secret_ref, str) or not secret_ref:
            raise SecretNotFoundError("Secret not found")

        # 查找
        if secret_ref not in self._store:
            raise SecretNotFoundError("Secret not found")

        # 返回新的 SecretValue 包装
        return SecretValue(self._store[secret_ref])

    def delete(self, secret_ref: str) -> None:
        """
        删除 Secret（幂等）
        
        不存在的引用执行 delete() 不报错。
        """
        self._store.pop(secret_ref, None)

    def exists(self, secret_ref: str) -> bool:
        """
        检查 Secret 是否存在
        
        Args:
            secret_ref: Secret 引用
        
        Returns:
            bool
        """
        return secret_ref in self._store

    def __repr__(self) -> str:
        """不显示 Secret、引用或数量"""
        return "InMemorySecretProvider()"

    def __str__(self) -> str:
        """不显示 Secret、引用或数量"""
        return "InMemorySecretProvider()"
