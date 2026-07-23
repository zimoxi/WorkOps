"""
WorkOps Audit Event Model — 审计事件模型
Sprint040: Audit Event System Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .event import AuditEventType, AuditSeverity
from .errors import InvalidAuditEventError


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """
    审计事件。不可变。
    """

    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    message: str
    operation_id: str | None = None
    job_id: str | None = None
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.event_id, str) or not self.event_id.strip():
            raise InvalidAuditEventError("event_id must be a non-empty string")
        if not isinstance(self.event_type, AuditEventType):
            raise InvalidAuditEventError("event_type must be an AuditEventType instance")
        if not isinstance(self.severity, AuditSeverity):
            raise InvalidAuditEventError("severity must be an AuditSeverity instance")
        if not isinstance(self.message, str) or not self.message.strip():
            raise InvalidAuditEventError("message must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
