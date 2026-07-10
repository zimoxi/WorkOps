"""
WorkOps Device Service
Sprint016: Repository Layer Foundation

调用 DeviceRepository
"""

from ..repositories import DeviceRepository


class DeviceService:
    """Device Service"""

    def __init__(self, repository: DeviceRepository):
        """
        初始化 Device Service
        
        Args:
            repository: DeviceRepository 实例
        """
        self.repository = repository

    def get_all_devices(self) -> list:
        """获取所有设备"""
        return self.repository.get_all()

    def get_device_by_id(self, device_id: str) -> dict:
        """根据 ID 获取设备"""
        return self.repository.get_by_id(device_id)
