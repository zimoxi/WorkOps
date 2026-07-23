"""
WorkOps Audit Event Types — 审计事件类型和严重级别
Sprint040: Audit Event System Foundation
"""

from enum import Enum


class AuditEventType(Enum):
    """审计事件类型。"""

    OPERATION_CREATED = "operation_created"
    OPERATION_STARTED = "operation_started"
    OPERATION_COMPLETED = "operation_completed"
    OPERATION_FAILED = "operation_failed"
    JOB_CREATED = "job_created"
    JOB_STARTED = "job_started"
    JOB_COMPLETED = "job_completed"
    JOB_FAILED = "job_failed"


class AuditSeverity(Enum):
    """审计事件严重级别。"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
