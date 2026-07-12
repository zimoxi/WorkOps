"""
WorkOps Mock Task Repository
Sprint016: Repository Layer Foundation
Sprint018: Execution Engine Foundation

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

    def transition_status(self, task_id: str, expected_status: str, new_status: str) -> bool:
        """
        原子状态转换（仅内存）
        
        Args:
            task_id: Task ID
            expected_status: 期望的当前状态
            new_status: 新状态
        
        Returns:
            bool: 转换是否成功
        """
        tasks = getattr(self.context, 'tasks', [])
        for task in tasks:
            if task.get('id') == task_id:
                if task.get('status') == expected_status:
                    task['status'] = new_status
                    return True
                return False
        return False
