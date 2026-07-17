"""
WorkOps Secret Provider Interface — 凭据提供者接口
Sprint021: Credential and Secret Management

仅允许：
- store(secret_value) -> secret_ref
- retrieve(secret_ref) -> SecretValue
- delete(secret_ref) -> None
- exists(secret_ref) -> bool

禁止：
- list()
- list_all()
- export()
- dump()
- get_all()
"""

from abc import ABC, abstractmethod

from .secret_value import SecretValue


class SecretProvider(ABC):
    """Secret Provider 接口"""

    @abstractmethod
    def store(self, secret_value) -> str:
        """
        存储 Secret，返回 secret_ref
        
        Args:
            secret_value: str 或 SecretValue
        
        Returns:
            secret_ref: 不可预测的引用字符串
        """
        pass

    @abstractmethod
    def retrieve(self, secret_ref: str) -> SecretValue:
        """
        获取 Secret
        
        Args:
            secret_ref: Secret 引用
        
        Returns:
            SecretValue
        
        Raises:
            SecretNotFoundError: 引用不存在
        """
        pass

    @abstractmethod
    def delete(self, secret_ref: str) -> None:
        """
        删除 Secret（幂等）
        
        不存在的引用执行 delete() 不报错。
        """
        pass

    @abstractmethod
    def exists(self, secret_ref: str) -> bool:
        """
        检查 Secret 是否存在
        
        Args:
            secret_ref: Secret 引用
        
        Returns:
            bool
        """
        pass
