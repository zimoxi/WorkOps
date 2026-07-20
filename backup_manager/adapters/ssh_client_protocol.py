"""
WorkOps SSH Client Protocol — 客户端接口
Sprint022: SSH Adapter Read-Only Foundation

公开方法仅：
  connect(config, username, password)
  run_query(query_id, timeout, max_output_bytes)
  get_host_fingerprint()
  close()

禁止任何公开 command 字符串入口。
"""

from abc import ABC, abstractmethod


class SSHClientProtocol(ABC):
    """SSH 客户端协议接口。"""

    @abstractmethod
    def connect(self, config, username, password):
        """连接到主机。config: SSHReadOnlyConnectionConfig"""
        pass

    @abstractmethod
    def get_host_fingerprint(self):
        """返回 HostFingerprint。仅连接后可用。"""
        pass

    @abstractmethod
    def run_query(self, query_id, timeout, max_output_bytes):
        """通过 QUERY_REGISTRY 执行固定命令。返回 SSHClientOutput。"""
        pass

    @abstractmethod
    def close(self):
        """关闭连接。幂等。"""
        pass
