"""
WorkOps Repository Layer
Sprint016: Repository Layer Foundation

Repository 接口和 MockRepository 实现
"""

from .interfaces import DeviceRepository, ResourceRepository, OperationRepository, TaskRepository
from .mock_device_repo import MockDeviceRepository
from .mock_resource_repo import MockResourceRepository
from .mock_operation_repo import MockOperationRepository
from .mock_task_repo import MockTaskRepository

__all__ = [
    "DeviceRepository",
    "ResourceRepository",
    "OperationRepository",
    "TaskRepository",
    "MockDeviceRepository",
    "MockResourceRepository",
    "MockOperationRepository",
    "MockTaskRepository",
]
