"""
WorkOps SSH Read-Only Adapter — 受控只读 SSH 适配器
Sprint022: SSH Adapter Read-Only Foundation

connect/disconnect/query/query_status/execute/get_host_fingerprint
execute() 永久拒绝。
query() 是唯一远程查询入口。
"""

import pathlib

from .base import BaseAdapter
from .ssh_errors import (
    SSHConfigurationError,
    SSHConnectionError,
    SSHQueryExecutionError,
    SSHQueryNotAllowedError,
    SSHAdapterError,
)
from .ssh_models import QUERY_REGISTRY, SSHReadOnlyConnectionConfig, SSHReadOnlyQueryResult
from .ssh_paramiko_client import ParamikoReadOnlyClient


class SSHReadOnlyAdapter(BaseAdapter):
    """SSH 只读适配器。"""

    def __init__(self, credential_metadata, secret_provider, client_factory=None):
        self._credential = credential_metadata
        self._secret_provider = secret_provider
        self._client_factory = client_factory or ParamikoReadOnlyClient
        self._client = None
        self._config = None
        self._connected = False

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------
    def connect(self, device):
        if self._connected:
            raise SSHConnectionError("Already connected")

        # 用户名严格校验
        username = self._credential.username
        if not isinstance(username, str) or not username.strip():
            raise SSHConfigurationError("username must be a non-empty string")
        username = username.strip()
        for ch in username:
            if ord(ch) < 32:
                raise SSHConfigurationError("username contains control characters")
        if "@" in username:
            raise SSHConfigurationError("username must not contain @")
        if " " in username:
            raise SSHConfigurationError("username must not contain spaces")
        if username.casefold() == "root":
            raise SSHConfigurationError("Root login is not allowed")

        # CredentialType 校验 — 枚举直接比较
        from ..credentials.model import CredentialType
        if self._credential.credential_type is not CredentialType.PASSWORD:
            raise SSHConfigurationError("Only password authentication is supported")

        # 构建配置
        config = SSHReadOnlyConnectionConfig.from_mapping(device)

        # 检查 known_hosts 文件存在且为普通文件
        kh = pathlib.Path(config.known_hosts_path)
        if not kh.is_file():
            raise SSHConfigurationError("known_hosts file not found")

        # 获取 Secret
        secret_value = None
        password = None
        client = None
        try:
            secret_value = self._secret_provider.retrieve(self._credential.secret_ref)
            password = secret_value.reveal()
            client = self._client_factory()
            client.connect(config, username, password)
            # 连接成功后才提交长期状态
            self._client = client
            self._config = config
            self._connected = True
            return True
        except SSHAdapterError:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            self._client = None
            self._config = None
            self._connected = False
            raise
        except Exception:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
            self._client = None
            self._config = None
            self._connected = False
            raise SSHConnectionError("Connection failed") from None
        finally:
            secret_value = None
            password = None

    # ------------------------------------------------------------------
    # disconnect
    # ------------------------------------------------------------------
    def disconnect(self):
        if not self._connected:
            return
        client = self._client
        self._client = None
        self._config = None
        self._connected = False
        if client:
            try:
                client.close()
            except Exception:
                raise SSHConnectionError("Failed to close connection cleanly") from None

    # ------------------------------------------------------------------
    # execute — 永久拒绝
    # ------------------------------------------------------------------
    def execute(self, command):
        """永久拒绝任意命令。不解析或检查 command。"""
        raise SSHQueryNotAllowedError("SSH command execution is not allowed")

    # ------------------------------------------------------------------
    # query_status
    # ------------------------------------------------------------------
    def query_status(self):
        return {"online": self._connected}

    # ------------------------------------------------------------------
    # query — 唯一远程查询入口
    # ------------------------------------------------------------------
    def query(self, query_id):
        if not self._connected or not self._client:
            raise SSHConnectionError("Not connected")
        if query_id not in QUERY_REGISTRY:
            raise SSHQueryNotAllowedError("SSH query is not allowed")

        from ..credentials.redaction import redact_text

        try:
            raw = self._client.run_query(
                query_id,
                self._config.query_timeout,
                self._config.max_output_bytes,
            )

            # 解码
            stdout_decoded = raw.stdout.decode("utf-8", errors="replace")
            stderr_decoded = raw.stderr.decode("utf-8", errors="replace")

            # Redaction
            stdout_redacted = redact_text(stdout_decoded)
            stderr_redacted = redact_text(stderr_decoded)

            # 再次按 UTF-8 字节限制到 10 KiB
            max_bytes = self._config.max_output_bytes
            stdout_final, stdout_trunc = self._truncate_utf8(stdout_redacted, max_bytes)
            stderr_final, stderr_trunc = self._truncate_utf8(stderr_redacted, max_bytes)

            return SSHReadOnlyQueryResult(
                query_id=query_id,
                success=(raw.exit_code == 0),
                stdout=stdout_final,
                stderr=stderr_final,
                exit_code=raw.exit_code,
                stdout_truncated=raw.stdout_truncated or stdout_trunc,
                stderr_truncated=raw.stderr_truncated or stderr_trunc,
                message="" if raw.exit_code == 0 else "Query failed",
            )
        except SSHAdapterError:
            raise
        except Exception:
            raise SSHQueryExecutionError("Query execution failed") from None

    def _truncate_utf8(self, text, max_bytes):
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text, False
        truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
        return truncated, True

    # ------------------------------------------------------------------
    # get_host_fingerprint
    # ------------------------------------------------------------------
    def get_host_fingerprint(self):
        if not self._connected or not self._client:
            raise SSHConnectionError("Not connected")
        return self._client.get_host_fingerprint()
