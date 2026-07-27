"""
WorkOps Audit Dashboard Provider — 审计仪表盘数据提供者
Sprint075: Dashboard Runtime Integration

Returns recent audit summary.
No secrets. No credentials. No private data.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuditSummary:
    """
    审计摘要。不可变。
    """

    total_events: int
    recent_events: int
    message: str


class AuditDashboardProvider(ABC):
    """
    审计仪表盘数据提供者接口。

    返回: AuditSummary

    不暴露: 密钥、凭证、私有数据
    """

    @abstractmethod
    def get_audit_summary(self) -> AuditSummary:
        """
        获取审计摘要。

        Returns:
            AuditSummary
        """
        ...
