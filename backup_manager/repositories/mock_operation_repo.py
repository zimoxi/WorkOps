"""
WorkOps Mock Operation Repository
Sprint016: Repository Layer Foundation

包装现有 AppContext Mock 数据
禁止复制新的 Mock 数据
"""

from .interfaces import OperationRepository


class MockOperationRepository(OperationRepository):
    """Mock Operation Repository 实现"""

    def __init__(self, context):
        """
        包装现有 AppContext 的 operations
        
        Args:
            context: AppContext 对象
        """
        self.context = context

    def get_all(self) -> list:
        """获取所有操作"""
        return getattr(self.context, 'operations', [])

    def get_by_id(self, operation_id: str) -> dict:
        """根据 ID 获取操作"""
        operations = getattr(self.context, 'operations', [])
        for operation in operations:
            if operation.get('id') == operation_id:
                return operation
        return None
