"""
WorkOps Repository Layer
Sprint016: Repository Layer Foundation
Sprint018: Execution Engine Foundation
Sprint020: Persistence Foundation
"""

from .interfaces import (
    DeviceRepository,
    ResourceRepository,
    OperationRepository,
    TaskRepository,
    WritableTaskRepository,
    ExecutionResultRepository,
)
from .mock_device_repo import MockDeviceRepository
from .mock_resource_repo import MockResourceRepository
from .mock_operation_repo import MockOperationRepository
from .mock_task_repo import MockTaskRepository
from .mock_result_repo import MockExecutionResultRepository
from .db_task_repo import DatabaseTaskRepository
from .db_result_repo import DatabaseExecutionResultRepository
from .provider import RepositoryProvider

__all__ = [
    "DeviceRepository",
    "ResourceRepository",
    "OperationRepository",
    "TaskRepository",
    "WritableTaskRepository",
    "ExecutionResultRepository",
    "MockDeviceRepository",
    "MockResourceRepository",
    "MockOperationRepository",
    "MockTaskRepository",
    "MockExecutionResultRepository",
    "DatabaseTaskRepository",
    "DatabaseExecutionResultRepository",
    "RepositoryProvider",
]
