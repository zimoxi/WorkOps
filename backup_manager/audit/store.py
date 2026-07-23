"""
WorkOps Audit Event Store Contract — 审计事件存储接口
Sprint040: Audit Event System Foundation

只定义接口。不实现存储。
"""

from abc import ABC, abstractmethod

from .model import AuditEvent


class AuditEventStore(ABC):
    """
    审计事件存储接口。

    只定义接口。不实现存储。
    """

    @abstractmethod
    def append(self, event: AuditEvent) -> None:
        """
        追加审计事件。

        Args:
            event: 审计事件
        """
        ...

    @abstractmethod
    def get(self, event_id: str) -> AuditEvent:
        """
        获取审计事件。

        Args:
            event_id: 事件 ID

        Returns:
            AuditEvent
        """
        ...

    @abstractmethod
    def list(self) -> list[AuditEvent]:
        """
        列出所有审计事件。

        Returns:
            list[AuditEvent]
        """
        ...
