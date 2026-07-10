"""
WorkOps MockAdapter — Mock 实现
Sprint017: Device Adapter Foundation

如果尚未连接，必须抛出 AdapterNotConnectedError
"""

from .base import BaseAdapter
from .errors import AdapterNotConnectedError


class MockAdapter(BaseAdapter):
    """Mock Adapter 实现"""

    def __init__(self):
        self.connected = False
        self.device = None

    def connect(self, device: dict) -> bool:
        """连接设备（Mock）"""
        self.device = device
        self.connected = True
        return True

    def disconnect(self) -> None:
        """断开连接（Mock）"""
        self.connected = False
        self.device = None

    def execute(self, command: str) -> dict:
        """执行命令（Mock）"""
        if not self.connected:
            raise AdapterNotConnectedError("Cannot execute: device not connected")
        return {
            "success": True,
            "stdout": f"MOCK: Executed '{command}'",
            "stderr": "",
            "exit_code": 0
        }

    def query_status(self) -> dict:
        """查询设备状态（Mock）"""
        if not self.connected:
            raise AdapterNotConnectedError("Cannot query status: device not connected")
        return {
            "online": True,
            "cpu_usage": 25.5,
            "memory_usage": 60.2,
            "disk_usage": 45.8
        }
