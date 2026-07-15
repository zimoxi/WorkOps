"""
WorkOps Mock Task Repository
Sprint016: Repository Layer Foundation
Sprint018: Execution Engine Foundation
Sprint020: Persistence Foundation

包装现有 AppContext Mock 数据
禁止复制新的 Mock 数据
"""

from .interfaces import WritableTaskRepository
from ..persistence.errors import PersistenceValidationError, RepositoryConflictError


# Task 允许的字段
TASK_FIELDS = {"id", "operation_id", "operation_name", "device_id", "status", "start_time", "end_time", "duration"}


class MockTaskRepository(WritableTaskRepository):
    """Mock Task Repository 实现"""

    # 合法状态转换
    ALLOWED_TRANSITIONS = {
        ("pending", "running"),
        ("pending", "cancelled"),
        ("running", "success"),
        ("running", "failed"),
    }

    def __init__(self, context):
        """
        包装现有 AppContext 的 tasks
        
        Args:
            context: AppContext 对象
        """
        self.context = context

    def get_all(self) -> list:
        """获取所有任务"""
        return list(getattr(self.context, 'tasks', []))

    def get_by_id(self, task_id: str) -> dict:
        """根据 ID 获取任务"""
        tasks = getattr(self.context, 'tasks', [])
        for task in tasks:
            if task.get('id') == task_id:
                return dict(task)
        return None

    def transition_status(self, task_id: str, expected_status: str, new_status: str) -> bool:
        """
        状态转换（单进程 Mock 环境中的条件状态转换）
        
        只允许合法转换：
        - pending → running
        - pending → cancelled
        - running → success
        - running → failed
        """
        if (expected_status, new_status) not in self.ALLOWED_TRANSITIONS:
            return False
        
        tasks = getattr(self.context, 'tasks', [])
        for task in tasks:
            if task.get('id') == task_id:
                if task.get('status') == expected_status:
                    task['status'] = new_status
                    return True
                return False
        return False

    def add(self, task: dict) -> None:
        """
        插入新 Task
        
        规则：
        - 严格接受冻结的 8 个字段
        - id 必须非空
        - status 必须等于 pending
        - ID 已存在时 RepositoryConflictError
        """
        # 校验字段
        unknown_fields = set(task.keys()) - TASK_FIELDS
        if unknown_fields:
            raise PersistenceValidationError(f"Unknown fields: {unknown_fields}")

        # 校验 id
        if not task.get("id"):
            raise PersistenceValidationError("id is required")

        # 校验 status
        if task.get("status") != "pending":
            raise PersistenceValidationError("status must be pending")

        # 检查 ID 是否存在
        tasks = getattr(self.context, 'tasks', [])
        for t in tasks:
            if t.get('id') == task.get('id'):
                raise RepositoryConflictError(f"Task {task['id']} already exists")

        # 插入
        tasks.append(dict(task))
