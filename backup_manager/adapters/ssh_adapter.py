"""
WorkOps SSHAdapter — SSH 连接占位类
Sprint017: Device Adapter Foundation

未实现，抛出 AdapterNotImplementedError
"""

from .base import BaseAdapter
from .errors import AdapterNotImplementedError


class SSHAdapter(BaseAdapter):
    """SSH Adapter 占位类（未实现）"""

    def connect(self, device: dict) -> bool:
        raise AdapterNotImplementedError("SSHAdapter")

    def disconnect(self) -> None:
        raise AdapterNotImplementedError("SSHAdapter")

    def execute(self, command: str) -> dict:
        raise AdapterNotImplementedError("SSHAdapter")

    def query_status(self) -> dict:
        raise AdapterNotImplementedError("SSHAdapter")
