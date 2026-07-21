"""
WorkOps PVE Client Contract — PVE 客户端接口
Sprint027: PVE ReadOnly Adapter

定义 PVE 客户端只读查询接口。
不实现网络连接。
"""

from abc import ABC, abstractmethod


class PVEClient(ABC):
    """
    PVE 客户端接口。

    只读查询。不实现网络连接。
    """

    @abstractmethod
    def get_nodes(self) -> list:
        """获取节点列表。"""
        ...

    @abstractmethod
    def get_storage(self, node: str) -> list:
        """获取节点存储列表。"""
        ...

    @abstractmethod
    def get_status(self, node: str) -> dict:
        """获取节点状态。"""
        ...
