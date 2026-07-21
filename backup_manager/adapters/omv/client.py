"""
WorkOps OMV Client Contract — OMV 客户端接口
Sprint028: OMV ReadOnly Adapter

定义 OMV 客户端只读查询接口。
不实现网络连接。
"""

from abc import ABC, abstractmethod


class OMVClient(ABC):
    """
    OMV 客户端接口。

    只读查询。不实现网络连接。
    """

    @abstractmethod
    def get_system_info(self) -> dict:
        """获取系统信息。"""
        ...

    @abstractmethod
    def get_storage(self) -> list:
        """获取存储列表。"""
        ...

    @abstractmethod
    def get_status(self) -> dict:
        """获取系统状态。"""
        ...
