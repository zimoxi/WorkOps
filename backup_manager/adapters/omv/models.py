"""
WorkOps OMV Models — OMV 数据模型
Sprint028: OMV ReadOnly Adapter

所有模型不可变。不包含 credential/connection 信息。
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OMVSystemInfo:
    """OMV 系统信息。不可变。"""

    hostname: str
    version: str
    kernel: str
    uptime: int
    cpu_model: str
    cpu_cores: int
    memory_total: int
    memory_used: int


@dataclass(frozen=True, slots=True)
class OMVStorageInfo:
    """OMV 存储信息。不可变。"""

    device: str
    mount_point: str
    filesystem: str
    total: int
    used: int
    available: int


@dataclass(frozen=True, slots=True)
class OMVStatus:
    """OMV 状态。不可变。"""

    hostname: str
    status: str
    cpu_usage: float
    memory_usage: float
    uptime: int
