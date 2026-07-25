"""
WorkOps Metrics Model — 指标模型
Sprint063: Monitoring Metrics Foundation

MetricType, MetricRecord, MetricQuery
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum

from .errors import InvalidMetricError


class MetricType(Enum):
    """指标类型。"""

    EXECUTION_COUNT = "execution_count"
    EXECUTION_DURATION = "execution_duration"
    BACKUP_DURATION = "backup_duration"
    RESTORE_DURATION = "restore_duration"
    HEALTH_STATUS = "health_status"
    RUNTIME_LATENCY = "runtime_latency"


@dataclass(frozen=True, slots=True)
class MetricRecord:
    """
    指标记录。不可变。
    """

    metric_id: str
    metric_type: MetricType
    value: float
    source_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.metric_id, str) or not self.metric_id.strip():
            raise InvalidMetricError("metric_id must be a non-empty string")
        if not isinstance(self.metric_type, MetricType):
            raise InvalidMetricError("metric_type must be a MetricType instance")
        if not isinstance(self.value, (int, float)):
            raise InvalidMetricError("value must be a number")
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise InvalidMetricError("source_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class MetricQuery:
    """
    指标查询。不可变。
    """

    metric_type: MetricType
    source_id: str | None = None

    def __post_init__(self):
        if not isinstance(self.metric_type, MetricType):
            raise InvalidMetricError("metric_type must be a MetricType instance")


def validate_metric_record(record: MetricRecord) -> None:
    """
    验证指标记录。

    Args:
        record: 指标记录

    Raises:
        InvalidMetricError: 验证失败
    """
    if not isinstance(record, MetricRecord):
        raise InvalidMetricError("record must be a MetricRecord instance")


def validate_metric_query(query: MetricQuery) -> None:
    """
    验证指标查询。

    Args:
        query: 指标查询

    Raises:
        InvalidMetricError: 验证失败
    """
    if not isinstance(query, MetricQuery):
        raise InvalidMetricError("query must be a MetricQuery instance")
