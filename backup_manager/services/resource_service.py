"""
WorkOps Resource Service
Sprint016: Repository Layer Foundation

调用 ResourceRepository
"""

from ..repositories import ResourceRepository


class ResourceService:
    """Resource Service"""

    def __init__(self, repository: ResourceRepository):
        """
        初始化 Resource Service
        
        Args:
            repository: ResourceRepository 实例
        """
        self.repository = repository

    def get_all_resources(self) -> list:
        """获取所有资源"""
        return self.repository.get_all()

    def get_resource_by_id(self, resource_id: str) -> dict:
        """根据 ID 获取资源"""
        return self.repository.get_by_id(resource_id)
