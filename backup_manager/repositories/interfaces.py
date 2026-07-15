"""
WorkOps Repository Interfaces — Repository 接口定义
Sprint016: Repository Layer Foundation
Sprint018: Execution Engine Foundation
Sprint020: Persistence Foundation

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

    @abstractmethod
    def transition_status(self, task_id: str, expected_status: str, new_status: str) -> bool:
        """
        原子状态转换（单进程环境中的条件状态转换）
        
        合法转换：
        - pending → running
        - pending → cancelled
        - running → success
        - running → failed
        
        Args:
            task_id: Task ID
            expected_status: 期望的当前状态
            new_status: 新状态
        
        Returns:
            bool: 转换是否成功
        """
        pass


class WritableTaskRepository(TaskRepository):
    """扩展接口：支持插入新 Task"""

    @abstractmethod
    def add(self, task: dict) -> None:
        """
        插入新 Task
        
        规则：
        - 严格接受冻结的 8 个字段
        - id 必须非空
        - status 必须等于 pending
        - 非 pending 状态全部拒绝
        - ID 已存在时 RepositoryConflictError
        - 不允许覆盖
        - 不允许 update/delete/patch
        """
        pass


class ExecutionResultRepository(ABC):
    """ExecutionResult Repository 接口"""

    @abstractmethod
    def save(self, result: dict) -> None:
        """
        保存 ExecutionResult
        
        规则：
        - 首次保存允许
        - 相同 task_id、相同内容再次保存：幂等 no-op
        - 相同 task_id、不同内容：RepositoryConflictError
        - 禁止静默覆盖
        """
        pass

    @abstractmethod
    def get_by_task_id(self, task_id: str) -> dict:
        """根据 task_id 获取"""
        pass

    @abstractmethod
    def get_all(self) -> list:
        """获取所有"""
        pass
