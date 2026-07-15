"""
WorkOps Mock ExecutionResult Repository
Sprint020: Persistence Foundation

包装现有 AppContext Mock 数据
"""

from .interfaces import ExecutionResultRepository
from ..persistence.errors import PersistenceValidationError, RepositoryConflictError


# ExecutionResult 允许的字段
RESULT_FIELDS = {"task_id", "status", "started_at", "finished_at", "duration", "stdout", "stderr", "exit_code", "message"}


class MockExecutionResultRepository(ExecutionResultRepository):
    """Mock ExecutionResult Repository 实现"""

    def __init__(self, context):
        """
        包装现有 AppContext 的 execution_results
        
        Args:
            context: AppContext 对象
        """
        self.context = context
        # 如果 context 没有 execution_results 属性，创建并写回
        if not hasattr(self.context, 'execution_results'):
            self.context.execution_results = []

    def save(self, result: dict) -> None:
        """
        保存 ExecutionResult
        
        规则：
        - 首次保存允许
        - 相同 task_id、相同内容：幂等 no-op
        - 相同 task_id、不同内容：RepositoryConflictError
        """
        # 校验字段
        unknown_fields = set(result.keys()) - RESULT_FIELDS
        if unknown_fields:
            raise PersistenceValidationError(f"Unknown fields: {unknown_fields}")

        results = getattr(self.context, 'execution_results', [])
        for i, r in enumerate(results):
            if r.get('task_id') == result.get('task_id'):
                if r == result:
                    return  # 幂等 no-op
                raise RepositoryConflictError(
                    f"Result for task {result['task_id']} already exists with different content"
                )
        results.append(dict(result))

    def get_by_task_id(self, task_id: str) -> dict:
        """根据 task_id 获取"""
        results = getattr(self.context, 'execution_results', [])
        for r in results:
            if r.get('task_id') == task_id:
                return dict(r)
        return None

    def get_all(self) -> list:
        """获取所有"""
        return list(getattr(self.context, 'execution_results', []))
