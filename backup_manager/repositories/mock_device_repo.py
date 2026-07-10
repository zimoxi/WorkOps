"""
WorkOps Mock Device Repository
Sprint016: Repository Layer Foundation

包装现有 AppContext Mock 数据
禁止复制新的 Mock 数据
"""

from .interfaces import DeviceRepository


class MockDeviceRepository(DeviceRepository):
    """Mock Device Repository 实现"""

    def __init__(self, context):
        """
        包装现有 AppContext 的 device_service
        
        Args:
            context: AppContext 对象
        """
        self.context = context

    def get_all(self) -> list:
        """获取所有设备"""
        return self.context.device_service.list_devices()

    def get_by_id(self, device_id: str) -> dict:
        """根据 ID 获取设备"""
        device = self.context.device_service.get_device(device_id)
        return device if device else None
