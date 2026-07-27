"""
WorkOps SSH Client Contract — SSH 客户端接口
Sprint067: Real Linux SSH Connector

只定义接口。不绑定 paramiko/asyncssh。
"""

from abc import ABC, abstractmethod

from .connection import SSHConnectionConfig


class SSHClient(ABC):
    """
    SSH 客户端接口。

    允许未来实现:
    - paramiko
    - asyncssh
    - native ssh wrapper

    不硬编码库依赖。
    """

    @abstractmethod
    def connect(self, config: SSHConnectionConfig) -> None:
        """
        建立 SSH 连接。

        Args:
            config: SSH 连接配置
        """
        ...

    @abstractmethod
    def close(self) -> None:
        """关闭 SSH 连接。"""
        ...
