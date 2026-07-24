"""
WorkOps Health Runtime Errors — 健康运行时错误
Sprint055: Health Runtime Integration Foundation
"""


class HealthRuntimeError(Exception):
    """健康运行时错误基类"""
    pass


class InvalidHealthExecutionRequestError(HealthRuntimeError):
    """无效健康执行请求"""
    pass


class HealthRuntimeConflictError(HealthRuntimeError):
    """健康运行时冲突"""
    def __init__(self, health_id: str):
        super().__init__(f"Health runtime already exists: {health_id}")


class HealthRuntimeUnavailableError(HealthRuntimeError):
    """健康运行时不可用"""
    pass
