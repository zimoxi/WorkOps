"""
WorkOps Adapter Capabilities — 能力声明
Sprint023: Adapter Runtime Integration Foundation
"""

from enum import Enum


class AdapterCapability(Enum):
    """Adapter 能力枚举。只允许只读查询类能力。"""

    STATUS_QUERY = "status_query"
    SYSTEM_QUERY = "system_query"
