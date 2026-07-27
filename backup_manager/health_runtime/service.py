"""
WorkOps Runtime Health Service — 运行时健康服务
Sprint076: Runtime Health Probe and Device Inventory

Aggregates probes. Provides dashboard data.
"""

from abc import ABC, abstractmethod


class RuntimeHealthService(ABC):
    """
    运行时健康服务接口。

    职责:
    - 调用探针
    - 收集健康结果
    - 提供仪表盘数据
    """

    @abstractmethod
    def check_all(self) -> list:
        """
        检查所有设备健康状态。

        Returns:
            list[RuntimeHealthResult]
        """
        ...
