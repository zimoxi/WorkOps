"""
WorkOps Adapter Type — 适配器类型枚举
Sprint046: Device Adapter Integration Foundation
"""

from enum import Enum


class AdapterType(Enum):
    """适配器类型。"""

    LINUX = "linux"
    PVE = "pve"
    OMV = "omv"
    NAS = "nas"
