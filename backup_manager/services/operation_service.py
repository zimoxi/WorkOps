"""
WorkOps Operation Service
Sprint016: Repository Layer Foundation

调用 OperationRepository
"""

from ..repositories import OperationRepository


class OperationService:
    """Operation Service"""

    def __init__(self, repository: OperationRepository):
        """
        初始化 Operation Service
        
        Args:
            repository: OperationRepository 实例
        """
        self.repository = repository

    def get_all_operations(self) -> list:
        """获取所有操作"""
        return self.repository.get_all()

    def get_operation_by_id(self, operation_id: str) -> dict:
        """根据 ID 获取操作"""
        return self.repository.get_by_id(operation_id)
