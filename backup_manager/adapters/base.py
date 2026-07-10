"""
WorkOps BaseAdapter — Device Adapter 抽象接口
Sprint017: Device Adapter Foundation
"""

from abc import ABC, abstractmethod


class BaseAdapter(ABC):
    """Device Adapter 抽象接口"""

    @abstractmethod
    def connect(self, device: dict) -> bool:
        """
        连接设备
        
        Args:
            device: 设备信息字典
        
        Returns:
            bool: 连接是否成功
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    def execute(self, command: str) -> dict:
        """
        执行命令
        
        Args:
            command: 要执行的命令
        
        Returns:
            dict: 执行结果
            {
                "success": bool,
                "stdout": str,
                "stderr": str,
                "exit_code": int
            }
        """
        pass

    @abstractmethod
    def query_status(self) -> dict:
        """
        查询设备状态
        
        Returns:
            dict: 设备状态
            {
                "online": bool,
                "cpu_usage": float,
                "memory_usage": float,
                "disk_usage": float
            }
        """
        pass
