"""
WorkOps Security Validator — 安全验证器
Sprint057: Runtime Security Hardening Foundation

SecurityValidator, RuntimeSecurityBoundary
"""

from abc import ABC, abstractmethod

from .model import SecurityContext
from .policy import RuntimePermission


class SecurityValidator(ABC):
    """
    安全验证器接口。

    只定义接口。不实现真实验证。
    """

    @abstractmethod
    def validate(self, context: SecurityContext) -> bool:
        """
        验证安全上下文。

        Args:
            context: 安全上下文

        Returns:
            bool
        """
        ...


class RuntimeSecurityBoundary(ABC):
    """
    运行时安全边界接口。

    只定义接口。不实现真实检查。
    """

    @abstractmethod
    def check(self, permission: RuntimePermission) -> bool:
        """
        检查运行时权限。

        Args:
            permission: 运行时权限

        Returns:
            bool
        """
        ...
