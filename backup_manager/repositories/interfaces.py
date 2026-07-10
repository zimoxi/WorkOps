"""
WorkOps Repository Interfaces — Repository 接口定义
Sprint016: Repository Layer Foundation

定义统一 Repository 接口
"""

from abc import ABC, abstractmethod


class DeviceRepository(ABC):
    """Device Repository 接口"""

    @abstractmethod
    def get_all(self) -> list:
        """获取所有设备"""
        pass

    @abstractmethod
    def get_by_id(self, device_id: str) -> dict:
        """根据 ID 获取设备"""
        pass


class ResourceRepository(ABC):
    """Resource Repository 接口"""

    @abstractmethod
    def get_all(self) -> list:
        """获取所有资源"""
        pass

    @abstractmethod
    def get_by_id(self, resource_id: str) -> dict:
        """根据 ID 获取资源"""
        pass


class OperationRepository(ABC):
    """Operation Repository 接口"""

    @abstractmethod
    def get_all(self) -> list:
        """获取所有操作"""
        pass

    @abstractmethod
    def get_by_id(self, operation_id: str) -> dict:
        """根据 ID 获取操作"""
        pass


class TaskRepository(ABC):
    """Task Repository 接口"""

    @abstractmethod
    def get_all(self) -> list:
        """获取所有任务"""
        pass

    @abstractmethod
    def get_by_id(self, task_id: str) -> dict:
        """根据 ID 获取任务"""
        pass
