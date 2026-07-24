"""
WorkOps Linux SSH Connector Contract — Linux SSH 连接器接口
Sprint058: Linux SSH Runtime Foundation

只定义接口。不实现真实 SSH 连接。
"""

from abc import ABC, abstractmethod

from .model import SSHSession
from .session import SSHExecutionRequest
from .result import SSHRuntimeResult


class LinuxSSHConnector(ABC):
    """
    Linux SSH 连接器接口。

    只定义接口。不实现真实 SSH 连接。
    """

    @abstractmethod
    def connect(self, session: SSHSession) -> None:
        """
        建立 SSH 连接。

        Args:
            session: SSH 会话
        """
        ...

    @abstractmethod
    def execute_readonly(self, request: SSHExecutionRequest) -> SSHRuntimeResult:
        """
        执行只读 SSH 命令。

        Args:
            request: SSH 执行请求

        Returns:
            SSHRuntimeResult
        """
        ...
