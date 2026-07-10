"""
WorkOps WinRMAdapter — WinRM 连接占位类
Sprint017: Device Adapter Foundation

未实现，抛出 AdapterNotImplementedError
"""

from .base import BaseAdapter
from .errors import AdapterNotImplementedError


class WinRMAdapter(BaseAdapter):
    """WinRM Adapter 占位类（未实现）"""

    def connect(self, device: dict) -> bool:
        raise AdapterNotImplementedError("WinRMAdapter")

    def disconnect(self) -> None:
        raise AdapterNotImplementedError("WinRMAdapter")

    def execute(self, command: str) -> dict:
        raise AdapterNotImplementedError("WinRMAdapter")

    def query_status(self) -> dict:
        raise AdapterNotImplementedError("WinRMAdapter")
