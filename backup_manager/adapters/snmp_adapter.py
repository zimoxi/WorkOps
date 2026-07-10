"""
WorkOps SNMPAdapter — SNMP 连接占位类
Sprint017: Device Adapter Foundation

未实现，抛出 AdapterNotImplementedError
"""

from .base import BaseAdapter
from .errors import AdapterNotImplementedError


class SNMPAdapter(BaseAdapter):
    """SNMP Adapter 占位类（未实现）"""

    def connect(self, device: dict) -> bool:
        raise AdapterNotImplementedError("SNMPAdapter")

    def disconnect(self) -> None:
        raise AdapterNotImplementedError("SNMPAdapter")

    def execute(self, command: str) -> dict:
        raise AdapterNotImplementedError("SNMPAdapter")

    def query_status(self) -> dict:
        raise AdapterNotImplementedError("SNMPAdapter")
