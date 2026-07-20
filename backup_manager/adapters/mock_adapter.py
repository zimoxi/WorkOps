"""
WorkOps MockAdapter — Mock 实现
Sprint017: Device Adapter Foundation
Sprint023: 新增 query() 支持 Runtime 集成

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

    def query(self, query_id: str):
        """
        查询（Mock）。返回 MockSSHReadOnlyQueryResult。

        仅用于 Runtime 集成测试。不调用真实 SSH。
        """
        if not self.connected:
            raise AdapterNotConnectedError("Cannot query: device not connected")
        from .ssh_models import SSHReadOnlyQueryResult
        return SSHReadOnlyQueryResult(
            query_id=query_id,
            success=True,
            stdout=f"mock-{query_id}",
            stderr="",
            exit_code=0,
            stdout_truncated=False,
            stderr_truncated=False,
            message="",
        )
