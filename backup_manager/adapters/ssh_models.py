"""
WorkOps SSH Models — 冻结数据模型和查询注册表
Sprint022: SSH Adapter Read-Only Foundation

所有模型不可变。QueryRegistry 使用 MappingProxyType。
"""

import base64
import hashlib
import math
import pathlib
from dataclasses import dataclass
from types import MappingProxyType

from .ssh_errors import SSHConfigurationError


# ---------------------------------------------------------------------------
# SSHReadOnlyConnectionConfig
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True, repr=False)
class SSHReadOnlyConnectionConfig:
    """SSH 连接配置（不可变）。repr/str 隐藏完整 known_hosts 路径。"""
    _host: str
    _port: int
    _known_hosts_path: str
    _connect_timeout: float
    _query_timeout: float
    _max_output_bytes: int

    @property
    def host(self):
        return self._host

    @property
    def port(self):
        return self._port

    @property
    def known_hosts_path(self):
        return self._known_hosts_path

    @property
    def connect_timeout(self):
        return self._connect_timeout

    @property
    def query_timeout(self):
        return self._query_timeout

    @property
    def max_output_bytes(self):
        return self._max_output_bytes

    def __repr__(self):
        return (
            f"SSHReadOnlyConnectionConfig("
            f"host={self._host!r}, port={self._port}, "
            f"known_hosts_path=<hidden>, "
            f"connect_timeout={self._connect_timeout}, "
            f"query_timeout={self._query_timeout}, "
            f"max_output_bytes={self._max_output_bytes}"
            f")"
        )

    def __str__(self):
        return self.__repr__()

    @classmethod
    def from_mapping(cls, mapping):
        """
        严格六字段集合。无默认值。未知/缺失字段拒绝。
        错误消息不回显任意输入字段。
        """
        if not isinstance(mapping, dict):
            raise SSHConfigurationError("Config must be a mapping")

        allowed = frozenset({
            "host", "port", "known_hosts_path",
            "connect_timeout", "query_timeout", "max_output_bytes",
        })
        extra = set(mapping.keys()) - allowed
        if extra:
            raise SSHConfigurationError("Unknown config fields present")
        missing = allowed - set(mapping.keys())
        if missing:
            raise SSHConfigurationError("Missing required config fields")

        host = mapping["host"]
        port = mapping["port"]
        kh_path = mapping["known_hosts_path"]
        connect_timeout = mapping["connect_timeout"]
        query_timeout = mapping["query_timeout"]
        max_output = mapping["max_output_bytes"]

        # --- host ---
        if not isinstance(host, str) or not host.strip():
            raise SSHConfigurationError("host must be a non-empty string")
        host = host.strip()
        # 拒绝 URL、CIDR、列表、user@host、控制字符和 shell 元字符
        _dangerous = set('/\\\n\r;|&$`(){}*?~@,')
        for ch in _dangerous:
            if ch in host:
                raise SSHConfigurationError("host contains invalid characters")
        # IPv6 方括号通过后单独检查
        if host.startswith("["):
            if not host.endswith("]") or len(host) < 3:
                raise SSHConfigurationError("host contains invalid characters")
            inner = host[1:-1]
            if not inner:
                raise SSHConfigurationError("host contains invalid characters")
            for ch in _dangerous:
                if ch in inner:
                    raise SSHConfigurationError("host contains invalid characters")

        # --- port ---
        if not isinstance(port, int) or isinstance(port, bool):
            raise SSHConfigurationError("port must be an integer")
        if port < 1 or port > 65535:
            raise SSHConfigurationError("port must be 1-65535")

        # --- known_hosts_path ---
        if not isinstance(kh_path, str) or not kh_path.strip():
            raise SSHConfigurationError("known_hosts_path must be a non-empty string")
        kh_path = kh_path.strip()

        # --- connect_timeout ---
        if not isinstance(connect_timeout, (int, float)) or isinstance(connect_timeout, bool):
            raise SSHConfigurationError("connect_timeout must be a number")
        if not math.isfinite(connect_timeout):
            raise SSHConfigurationError("connect_timeout must be finite")
        if connect_timeout <= 0 or connect_timeout > 300:
            raise SSHConfigurationError("connect_timeout must be 0 < x <= 300")

        # --- query_timeout ---
        if not isinstance(query_timeout, (int, float)) or isinstance(query_timeout, bool):
            raise SSHConfigurationError("query_timeout must be a number")
        if not math.isfinite(query_timeout):
            raise SSHConfigurationError("query_timeout must be finite")
        if query_timeout <= 0 or query_timeout > 300:
            raise SSHConfigurationError("query_timeout must be 0 < x <= 300")

        # --- max_output_bytes ---
        if not isinstance(max_output, int) or isinstance(max_output, bool):
            raise SSHConfigurationError("max_output_bytes must be an integer")
        if max_output < 1 or max_output > 10240:
            raise SSHConfigurationError("max_output_bytes must be 1-10240")

        return cls(
            _host=host,
            _port=port,
            _known_hosts_path=kh_path,
            _connect_timeout=float(connect_timeout),
            _query_timeout=float(query_timeout),
            _max_output_bytes=max_output,
        )


# ---------------------------------------------------------------------------
# SSHClientOutput — 替代五元素 tuple
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SSHClientOutput:
    """Client 级别原始输出（字节）。"""
    exit_code: int
    stdout: bytes
    stderr: bytes
    stdout_truncated: bool
    stderr_truncated: bool


# ---------------------------------------------------------------------------
# SSHReadOnlyQueryResult — Adapter 级别输出
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class SSHReadOnlyQueryResult:
    """Adapter 级别查询结果（已脱敏、已截断）。"""
    query_id: str
    success: bool
    stdout: str
    stderr: str
    exit_code: int
    stdout_truncated: bool
    stderr_truncated: bool
    message: str


# ---------------------------------------------------------------------------
# HostFingerprint
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class HostFingerprint:
    algorithm: str
    sha256_fingerprint: str
    host: str
    port: int


def compute_host_fingerprint(key, host, port):
    """
    SHA256:Base64WithoutPadding
    host/port 来自已验证的 ConnectionConfig。
    禁止 get_fingerprint().hex()。
    """
    digest = hashlib.sha256(key.asbytes()).digest()
    encoded = base64.b64encode(digest).decode("ascii").rstrip("=")
    return HostFingerprint(
        algorithm="SHA256",
        sha256_fingerprint=f"SHA256:{encoded}",
        host=host,
        port=port,
    )


# ---------------------------------------------------------------------------
# QueryDefinition & QUERY_REGISTRY
# ---------------------------------------------------------------------------

@dataclass(frozen=True, slots=True)
class QueryDefinition:
    query_id: str
    command: str
    description: str


QUERY_REGISTRY = MappingProxyType({
    "system.hostname": QueryDefinition(
        query_id="system.hostname",
        command="hostname",
        description="System hostname",
    ),
    "system.uptime": QueryDefinition(
        query_id="system.uptime",
        command="uptime -p",
        description="System uptime",
    ),
    "system.os": QueryDefinition(
        query_id="system.os",
        command="uname -srm",
        description="OS information",
    ),
})
