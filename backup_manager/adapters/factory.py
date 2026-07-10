"""
WorkOps AdapterFactory — Adapter 工厂方法
Sprint017: Device Adapter Foundation

只暴露 create(adapter_type)
暂不实现 register()
"""

from .mock_adapter import MockAdapter
from .ssh_adapter import SSHAdapter
from .winrm_adapter import WinRMAdapter
from .snmp_adapter import SNMPAdapter
from .errors import AdapterNotImplementedError


class AdapterFactory:
    """Adapter 工厂方法"""

    _adapters = {
        "mock": MockAdapter,
        "ssh": SSHAdapter,
        "winrm": WinRMAdapter,
        "snmp": SNMPAdapter,
    }

    @classmethod
    def create(cls, adapter_type: str):
        """
        创建 Adapter 实例
        
        Args:
            adapter_type: Adapter 类型 (mock, ssh, winrm, snmp)
        
        Returns:
            BaseAdapter: Adapter 实例
        
        Raises:
            AdapterNotImplementedError: 不支持的 Adapter 类型
        """
        adapter_class = cls._adapters.get(adapter_type)
        if not adapter_class:
            raise AdapterNotImplementedError(f"Unknown adapter type: {adapter_type}")
        return adapter_class()
