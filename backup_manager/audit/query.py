"""
WorkOps Audit Query Model — 审计查询模型
Sprint040: Audit Event System Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .event import AuditEventType


@dataclass(frozen=True, slots=True)
class AuditQuery:
    """
    审计查询。不可变。
    """

    event_type: AuditEventType | None = None
    operation_id: str | None = None
    job_id: str | None = None
