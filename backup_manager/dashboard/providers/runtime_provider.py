"""
WorkOps Runtime Dashboard Provider — 运行时仪表盘数据提供者
Sprint075: Dashboard Runtime Integration

Collects Linux/PVE/OMV runtime status.
No credentials. No secrets. No connection details.
"""

from abc import ABC, abstractmethod

from ..models import RuntimeOverview


class RuntimeDashboardProvider(ABC):
    """
    运行时仪表盘数据提供者接口。

    收集:
    - Linux Runtime status
    - PVE Runtime status
    - OMV Runtime status

    返回: RuntimeOverview 列表

    不暴露: 凭证、密钥、连接详情
    """

    @abstractmethod
    def get_runtime_overview(self) -> list:
        """
        获取运行时概览。

        Returns:
            list[RuntimeOverview]
        """
        ...
