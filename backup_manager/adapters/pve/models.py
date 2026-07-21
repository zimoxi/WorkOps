"""
WorkOps PVE Models — PVE 数据模型
Sprint027: PVE ReadOnly Adapter

所有模型不可变。不包含 credential/connection 信息。
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PVENodeInfo:
    """PVE 节点信息。不可变。"""

    node: str
    status: str
    cpu_cores: int
    memory_total: int
    memory_used: int
    uptime: int


@dataclass(frozen=True, slots=True)
class PVEStorageInfo:
    """PVE 存储信息。不可变。"""

    storage: str
    node: str
    storage_type: str
    total: int
    used: int
    active: bool


@dataclass(frozen=True, slots=True)
class PVEStatus:
    """PVE 状态。不可变。"""

    node: str
    status: str
    cpu_usage: float
    memory_usage: float
    uptime: int
