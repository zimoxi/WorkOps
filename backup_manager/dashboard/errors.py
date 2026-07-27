"""
WorkOps Dashboard Errors — 仪表盘错误
Sprint073: Web Dashboard Foundation
"""


class DashboardError(Exception):
    """仪表盘错误基类"""
    pass


class DashboardUnavailableError(DashboardError):
    """仪表盘不可用"""
    pass


class InvalidDashboardRequestError(DashboardError):
    """无效仪表盘请求"""
    pass
