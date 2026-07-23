"""
WorkOps Health Errors — 健康监控错误
Sprint043: Device Health Monitoring Foundation
"""


class HealthError(Exception):
    """健康监控错误基类"""
    pass


class InvalidHealthRequestError(HealthError):
    """无效健康检查请求"""
    pass


class HealthCheckConflictError(HealthError):
    """健康检查冲突"""
    def __init__(self, check_id: str):
        super().__init__(f"Health check already exists: {check_id}")


class HealthCheckNotFoundError(HealthError):
    """健康检查未找到"""
    def __init__(self, check_id: str):
        super().__init__(f"Health check not found: {check_id}")
