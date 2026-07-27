"""
WorkOps Runtime Health Probe — 运行时健康探针
Sprint076: Runtime Health Probe and Device Inventory

Defines health check boundary. No direct credentials.
"""

from abc import ABC, abstractmethod

from .health_models import RuntimeDevice, RuntimeHealthResult


class RuntimeHealthProbe(ABC):
    """
    运行时健康探针接口。

    定义健康检查边界。不直接访问凭证。
    """

    @abstractmethod
    def check(self, device: RuntimeDevice) -> RuntimeHealthResult:
        """
        检查设备健康状态。

        Args:
            device: 运行时设备

        Returns:
            RuntimeHealthResult
        """
        ...
