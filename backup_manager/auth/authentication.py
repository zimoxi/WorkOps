"""
WorkOps Authentication Provider Contract — 认证提供者接口
Sprint072: Authentication RBAC Foundation

只定义接口。不实现密码登录/JWT/OAuth/LDAP。
"""

from abc import ABC, abstractmethod

from .identity import Identity


class AuthenticationProvider(ABC):
    """
    认证提供者接口。

    只定义接口。不实现密码登录/JWT/OAuth/LDAP。
    """

    @abstractmethod
    def authenticate(self, identity_data) -> Identity:
        """
        认证用户。

        Args:
            identity_data: 认证数据

        Returns:
            Identity
        """
        ...
