"""
WorkOps Metrics Errors — 指标错误
Sprint063: Monitoring Metrics Foundation
"""


class MetricsError(Exception):
    """指标错误基类"""
    pass


class InvalidMetricError(MetricsError):
    """无效指标"""
    pass


class MetricsUnavailableError(MetricsError):
    """指标不可用"""
    pass


class MetricsQueryError(MetricsError):
    """指标查询错误"""
    pass
