"""
WorkOps Mock Resource Repository
Sprint016: Repository Layer Foundation

包装现有 AppContext Mock 数据
禁止复制新的 Mock 数据
"""

from .interfaces import ResourceRepository


class MockResourceRepository(ResourceRepository):
    """Mock Resource Repository 实现"""

    def __init__(self, context):
        """
        包装现有 AppContext 的 resources
        
        Args:
            context: AppContext 对象
        """
        self.context = context

    def get_all(self) -> list:
        """获取所有资源"""
        return getattr(self.context, 'resources', [])

    def get_by_id(self, resource_id: str) -> dict:
        """根据 ID 获取资源"""
        resources = getattr(self.context, 'resources', [])
        for resource in resources:
            if resource.get('id') == resource_id:
                return resource
        return None
