"""
WorkOps Task Service
Sprint016: Repository Layer Foundation

调用 TaskRepository
"""

from ..repositories import TaskRepository


class TaskService:
    """Task Service"""

    def __init__(self, repository: TaskRepository):
        """
        初始化 Task Service
        
        Args:
            repository: TaskRepository 实例
        """
        self.repository = repository

    def get_all_tasks(self) -> list:
        """获取所有任务"""
        return self.repository.get_all()

    def get_task_by_id(self, task_id: str) -> dict:
        """根据 ID 获取任务"""
        return self.repository.get_by_id(task_id)
