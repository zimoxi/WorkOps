"""
WorkOps Audit Errors — 审计错误
Sprint040: Audit Event System Foundation
"""


class AuditError(Exception):
    """审计错误基类"""
    pass


class InvalidAuditEventError(AuditError):
    """无效审计事件"""
    pass


class AuditEventConflictError(AuditError):
    """审计事件冲突"""
    def __init__(self, event_id: str):
        super().__init__(f"Audit event already exists: {event_id}")


class AuditEventNotFoundError(AuditError):
    """审计事件未找到"""
    def __init__(self, event_id: str):
        super().__init__(f"Audit event not found: {event_id}")
