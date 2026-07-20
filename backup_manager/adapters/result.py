"""
WorkOps Adapter Query Result — 统一查询结果
Sprint023: Adapter Runtime Integration Foundation

标准化查询结果，不包含 command/stdout/stderr/password/secret_ref。
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AdapterQueryResult:
    """统一查询结果。不可变。"""

    query_id: str
    success: bool
    data: dict
    message: str
    timestamp: str
