"""
WorkOps Mock Task Repository
Sprint016: Repository Layer Foundation

包装现有 AppContext Mock 数据
禁止复制新的 Mock 数据
"""

from .interfaces import TaskRepository


class MockTaskRepository(TaskRepository):
    """Mock Task Repository 实现"""

    def __init__(self, context):
        """
        包装现有 AppContext 的 tasks
        
        Args:
            context: AppContext 对象
        """
        self.context = context

    def get_all(self) -> list:
        """获取所有任务"""
        return getattr(self.context, 'tasks', [])

    def get_by_id(self, task_id: str) -> dict:
        """根据 ID 获取任务"""
        tasks = getattr(self.context, 'tasks', [])
        for task in tasks:
            if task.get('id') == task_id:
                return task
        return None
