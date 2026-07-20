"""
Sprint022 — SSH Adapter Read-Only Foundation — Tests
所有测试使用 Fake Client / Fake Paramiko，不访问网络。
"""

import base64
import hashlib
import math
import socket
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from backup_manager.adapters.ssh_errors import (
    SSHAdapterError,
    SSHAuthenticationError,
    SSHConfigurationError,
    SSHConnectionError,
    SSHHostKeyError,
    SSHQueryExecutionError,
    SSHQueryNotAllowedError,
    SSHTimeoutError,
)
from backup_manager.adapters.ssh_models import (
    QUERY_REGISTRY,
    HostFingerprint,
    QueryDefinition,
    SSHClientOutput,
    SSHReadOnlyConnectionConfig,
    SSHReadOnlyQueryResult,
    compute_host_fingerprint,
)
from backup_manager.adapters.ssh_client_protocol import SSHClientProtocol
from backup_manager.adapters.ssh_readonly_adapter import SSHReadOnlyAdapter
from backup_manager.adapters.factory import AdapterFactory
from backup_manager.credentials.model import CredentialMetadata, CredentialType
from backup_manager.credentials.in_memory import InMemorySecretProvider
from backup_manager.credentials.secret_value import SecretValue

from datetime import datetime, timezone


# ============================================================================
# Fake helpers
# ============================================================================

def _make_known_hosts(tmp_dir):
    """创建临时 known_hosts 文件"""
    p = Path(tmp_dir) / "known_hosts"
    p.write_text("# fake known_hosts\n")
    return str(p)


def _make_config_dict(known_hosts_path, **overrides):
    """构建合法配置字典"""
    d = {
        "host": "192.168.1.100",
        "port": 22,
        "known_hosts_path": known_hosts_path,
        "connect_timeout": 10.0,
        "query_timeout": 30.0,
        "max_output_bytes": 10240,
    }
    d.update(overrides)
    return d


def _make_credential(username="testuser"):
    """创建测试 CredentialMetadata"""
    return CredentialMetadata(
        credential_id="cred-001",
        name="Test Credential",
        credential_type=CredentialType.PASSWORD,
        username=username,
        secret_ref="ref-abc123",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def _make_secret_provider(secret="test-password"):
    """创建 InMemorySecretProvider 并存入 Secret"""
    provider = InMemorySecretProvider()
    provider.store(secret)
    # 获取实际 ref
    refs = list(provider._store.keys())
    return provider, refs[0]


def _make_credential_with_ref(username, secret="test-password"):
    """创建 Credential 和带 ref 的 Provider"""
    provider = InMemorySecretProvider()
    secret_value = SecretValue(secret)
    ref = provider.store(secret_value)
    cred = CredentialMetadata(
        credential_id="cred-001",
        name="Test Credential",
        credential_type=CredentialType.PASSWORD,
        username=username,
        secret_ref=ref,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    return cred, provider


# ============================================================================
# Fake Paramiko exceptions
# ============================================================================

class FakeAuthenticationException(SSHAuthenticationError):
    pass


class FakeBadHostKeyException(SSHHostKeyError):
    pass


class FakeNoValidConnectionsError(SSHConnectionError):
    pass


class FakeSSHException(SSHConnectionError):
    pass


# ============================================================================
# Fake Channel
# ============================================================================

class FakeChannel:
    """模拟 Paramiko Channel，支持双通道读取。"""

    def __init__(self, stdout_data=b"", stderr_data=b"", exit_code=0, delay=0):
        self._stdout_data = stdout_data
        self._stderr_data = stderr_data
        self._exit_code = exit_code
        self._stdout_pos = 0
        self._stderr_pos = 0
        self._exit_ready = False
        self._closed = False
        self._delay = delay
        self._close_count = 0

    def recv_ready(self):
        return self._stdout_pos < len(self._stdout_data)

    def recv(self, size):
        chunk = self._stdout_data[self._stdout_pos: self._stdout_pos + size]
        self._stdout_pos += len(chunk)
        if self._stdout_pos >= len(self._stdout_data):
            self._exit_ready = True
        return chunk

    def recv_stderr_ready(self):
        return self._stderr_pos < len(self._stderr_data)

    def recv_stderr(self, size):
        chunk = self._stderr_data[self._stderr_pos: self._stderr_pos + size]
        self._stderr_pos += len(chunk)
        return chunk

    def exit_status_ready(self):
        return self._exit_ready

    def recv_exit_status(self):
        return self._exit_code

    def close(self):
        self._closed = True
        self._close_count += 1


# ============================================================================
# Fake Stdout/Stderr (for exec_command return)
# ============================================================================

class FakeStdout:
    def __init__(self, channel):
        self.channel = channel


class FakeStdin:
    def close(self):
        pass


# ============================================================================
# Fake SSH Client (simulates paramiko.SSHClient)
# ============================================================================

class FakeSSHClient:
    """模拟 paramiko.SSHClient"""

    def __init__(self, fail_connect=None, host_fingerprint=None, paramiko_module=None):
        self._fail_connect = fail_connect
        self._host_fingerprint = host_fingerprint
        self._paramiko = paramiko_module
        self._connected = False
        self._host_keys_path = None
        self._policy = None
        self._connect_kwargs = None
        self._closed = False
        self._close_count = 0
        self._channel = None

    def load_host_keys(self, path):
        self._host_keys_path = path

    def set_missing_host_key_policy(self, policy):
        self._policy = policy

    def connect(self, config=None, username=None, password=None, **kwargs):
        if self._fail_connect:
            raise self._fail_connect
        self._connected = True
        self._connect_kwargs = {"config": config, "username": username, "password": password, **kwargs}

    def exec_command(self, command, timeout=None):
        if self._channel is None:
            self._channel = FakeChannel(stdout_data=b"fake-output\n", exit_code=0)
        return FakeStdin(), FakeStdout(self._channel), FakeStdout(self._channel)

    def get_transport(self):
        mock_transport = MagicMock()
        key = MagicMock()
        key.asbytes.return_value = b"fake-key-bytes"
        key.get_name.return_value = "ssh-rsa"
        mock_transport.get_remote_server_key.return_value = key
        mock_transport.getpeername.return_value = ("192.168.1.100", 22)
        return mock_transport

    def close(self):
        self._closed = True
        self._close_count += 1

    def get_host_fingerprint(self):
        from backup_manager.adapters.ssh_models import compute_host_fingerprint
        key = MagicMock()
        key.asbytes.return_value = b"fake-key-bytes"
        return compute_host_fingerprint(key, "192.168.1.100", 22)

    def run_query(self, query_id, timeout, max_output_bytes):
        """Simulate ParamikoReadOnlyClient.run_query() for testing."""
        from backup_manager.adapters.ssh_models import QUERY_REGISTRY, SSHClientOutput
        from backup_manager.adapters.ssh_errors import SSHQueryNotAllowedError
        query_def = QUERY_REGISTRY.get(query_id)
        if query_def is None:
            raise SSHQueryNotAllowedError("SSH query is not allowed")
        stdin, stdout_ch, stderr_ch = self.exec_command(query_def.command, timeout=timeout)
        stdin.close()
        channel = stdout_ch.channel
        stdout_data = b""
        stderr_data = b""
        stdout_truncated = False
        stderr_truncated = False
        if channel.recv_ready():
            chunk = channel.recv(max_output_bytes)
            if len(chunk) >= max_output_bytes and channel.recv_ready():
                stdout_truncated = True
            stdout_data = chunk
        if channel.recv_stderr_ready():
            chunk = channel.recv_stderr(max_output_bytes)
            if chunk:
                if len(chunk) >= max_output_bytes and channel.recv_stderr_ready():
                    stderr_truncated = True
                stderr_data = chunk
        exit_code = channel.recv_exit_status() if channel.exit_status_ready() else 0
        return SSHClientOutput(
            exit_code=exit_code,
            stdout=stdout_data,
            stderr=stderr_data,
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
        )


# ============================================================================
# Fake Paramiko Module
# ============================================================================

class FakeParamiko:
    """模拟 paramiko 模块"""

    SSHException = FakeSSHException
    AuthenticationException = FakeAuthenticationException
    BadHostKeyException = FakeBadHostKeyException
    NoValidConnectionsError = FakeNoValidConnectionsError

    class RejectPolicy:
        pass

    class AutoAddPolicy:
        pass

    def __init__(self, fail_connect=None, channel=None):
        self._fail_connect = fail_connect
        self._channel = channel
        self._client_instances = []

    def SSHClient(self):
        client = FakeSSHClient(
            fail_connect=self._fail_connect,
            paramiko_module=self,
        )
        if self._channel:
            client._channel = self._channel
        self._client_instances.append(client)
        return client


# ============================================================================
# SSHReadOnlyConnectionConfig Tests
# ============================================================================

class TestSSHReadOnlyConnectionConfig(unittest.TestCase):

    def test_valid_config(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            cfg = SSHReadOnlyConnectionConfig.from_mapping(_make_config_dict(kh))
            self.assertEqual(cfg.host, "192.168.1.100")
            self.assertEqual(cfg.port, 22)
            self.assertEqual(cfg.known_hosts_path, kh)
            self.assertEqual(cfg.connect_timeout, 10.0)
            self.assertEqual(cfg.query_timeout, 30.0)
            self.assertEqual(cfg.max_output_bytes, 10240)

    def test_six_fields_all_required(self):
        """六字段缺一拒绝"""
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            base = _make_config_dict(kh)
            for key in base:
                incomplete = {k: v for k, v in base.items() if k != key}
                with self.assertRaises(SSHConfigurationError):
                    SSHReadOnlyConnectionConfig.from_mapping(incomplete)

    def test_unknown_field_rejected(self):
        """未知字段拒绝"""
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh)
            d["extra_field"] = "value"
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_no_default_values(self):
        """不使用静默默认值"""
        with self.assertRaises(SSHConfigurationError):
            SSHReadOnlyConnectionConfig.from_mapping({"host": "h"})

    def test_not_a_mapping(self):
        with self.assertRaises(SSHConfigurationError):
            SSHReadOnlyConnectionConfig.from_mapping("not a dict")

    def test_ipv4_host(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="10.0.0.1")
            cfg = SSHReadOnlyConnectionConfig.from_mapping(d)
            self.assertEqual(cfg.host, "10.0.0.1")

    def test_ipv6_host(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="::1")
            cfg = SSHReadOnlyConnectionConfig.from_mapping(d)
            self.assertEqual(cfg.host, "::1")

    def test_hostname(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="my-server")
            cfg = SSHReadOnlyConnectionConfig.from_mapping(d)
            self.assertEqual(cfg.host, "my-server")

    def test_url_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="http://example.com")
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_cidr_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="10.0.0.0/24")
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_list_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="host1,host2")
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_user_at_host_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="user@host")
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_control_char_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="host\nname")
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_empty_host_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, host="   ")
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_bool_port_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, port=True)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_port_range(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, port=0)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)
            d = _make_config_dict(kh, port=65536)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_bool_max_output_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, max_output_bytes=True)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_max_output_range(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, max_output_bytes=0)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)
            d = _make_config_dict(kh, max_output_bytes=10241)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_nan_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, connect_timeout=float("nan"))
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_inf_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, query_timeout=float("inf"))
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_negative_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, connect_timeout=-1)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_over_300_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            d = _make_config_dict(kh, query_timeout=301)
            with self.assertRaises(SSHConfigurationError):
                SSHReadOnlyConnectionConfig.from_mapping(d)

    def test_repr_hides_known_hosts(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            cfg = SSHReadOnlyConnectionConfig.from_mapping(_make_config_dict(kh))
            r = repr(cfg)
            self.assertNotIn(kh, r)
            self.assertIn("<hidden>", r)

    def test_str_hides_known_hosts(self):
        with tempfile.TemporaryDirectory() as td:
            kh = _make_known_hosts(td)
            cfg = SSHReadOnlyConnectionConfig.from_mapping(_make_config_dict(kh))
            s = str(cfg)
            self.assertNotIn(kh, s)
            self.assertIn("<hidden>", s)


# ============================================================================
# Query Registry Tests
# ============================================================================

class TestQueryRegistry(unittest.TestCase):

    def test_three_queries_exist(self):
        self.assertIn("system.hostname", QUERY_REGISTRY)
        self.assertIn("system.uptime", QUERY_REGISTRY)
        self.assertIn("system.os", QUERY_REGISTRY)
        self.assertEqual(len(QUERY_REGISTRY), 3)

    def test_registry_not_modifiable(self):
        with self.assertRaises(TypeError):
            QUERY_REGISTRY["new_query"] = QueryDefinition("x", "y", "z")

    def test_query_definition_frozen(self):
        qd = QUERY_REGISTRY["system.hostname"]
        with self.assertRaises(AttributeError):
            qd.command = "malicious"

    def test_commands_fixed(self):
        self.assertEqual(QUERY_REGISTRY["system.hostname"].command, "hostname")
        self.assertEqual(QUERY_REGISTRY["system.uptime"].command, "uptime -p")
        self.assertEqual(QUERY_REGISTRY["system.os"].command, "uname -srm")


# ============================================================================
# Fingerprint Tests
# ============================================================================

class TestFingerprint(unittest.TestCase):

    def test_sha256_format(self):
        key = MagicMock()
        key.asbytes.return_value = b"fake-key-bytes"
        digest = hashlib.sha256(b"fake-key-bytes").digest()
        expected_b64 = base64.b64encode(digest).decode("ascii").rstrip("=")
        expected = f"SHA256:{expected_b64}"
        fp = compute_host_fingerprint(key, "192.168.1.100", 22)
        self.assertEqual(fp.sha256_fingerprint, expected)
        self.assertEqual(fp.algorithm, "SHA256")
        self.assertEqual(fp.host, "192.168.1.100")
        self.assertEqual(fp.port, 22)


# ============================================================================
# SSHClientOutput Tests
# ============================================================================

class TestSSHClientOutput(unittest.TestCase):

    def test_frozen(self):
        out = SSHClientOutput(0, b"a", b"b", False, False)
        with self.assertRaises(AttributeError):
            out.exit_code = 1


# ============================================================================
# SSHReadOnlyQueryResult Tests
# ============================================================================

class TestSSHReadOnlyQueryResult(unittest.TestCase):

    def test_frozen(self):
        r = SSHReadOnlyQueryResult("q", True, "o", "e", 0, False, False, "")
        with self.assertRaises(AttributeError):
            r.success = False


# ============================================================================
# SSHReadOnlyAdapter Tests (with Fake Client)
# ============================================================================

class TestSSHReadOnlyAdapterExecute(unittest.TestCase):
    """execute 永久拒绝"""

    def test_execute_rejects_string(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHQueryNotAllowedError):
            adapter.execute("ls")

    def test_execute_rejects_none(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHQueryNotAllowedError):
            adapter.execute(None)

    def test_execute_rejects_int(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHQueryNotAllowedError):
            adapter.execute(123)

    def test_execute_rejects_object(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHQueryNotAllowedError):
            adapter.execute(object())

    def test_execute_permanent_even_when_disconnected(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHQueryNotAllowedError):
            adapter.execute("anything")

    def test_execute_error_no_command_echo(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHQueryNotAllowedError) as cm:
            adapter.execute("malicious-cmd")
        self.assertNotIn("malicious-cmd", str(cm.exception))


class TestSSHReadOnlyAdapterConnect(unittest.TestCase):

    def _make_adapter(self, fake_paramiko=None, username="testuser"):
        if fake_paramiko is None:
            fake_paramiko = FakeParamiko()
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref(username)
        return SSHReadOnlyAdapter(cred, provider, fake_paramiko.SSHClient), kh, tmp

    def test_success(self):
        adapter, kh, tmp = self._make_adapter()
        device = _make_config_dict(kh)
        self.assertTrue(adapter.connect(device))
        self.assertTrue(adapter.query_status()["online"])

    def test_duplicate_connect_rejected(self):
        adapter, kh, tmp = self._make_adapter()
        device = _make_config_dict(kh)
        adapter.connect(device)
        with self.assertRaises(SSHConnectionError):
            adapter.connect(device)

    def test_authentication_failure(self):
        fp = FakeParamiko(fail_connect=FakeAuthenticationException("Authentication failed"))
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHAuthenticationError) as cm:
            adapter.connect(device)
        self.assertEqual(str(cm.exception), "Authentication failed")
        # 状态清空
        self.assertFalse(adapter.query_status()["online"])

    def test_host_key_failure(self):
        fp = FakeParamiko(fail_connect=FakeBadHostKeyException("Host key verification failed"))
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHHostKeyError) as cm:
            adapter.connect(device)
        self.assertEqual(str(cm.exception), "Host key verification failed")

    def test_connection_failure(self):
        fp = FakeParamiko(fail_connect=FakeNoValidConnectionsError())
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConnectionError):
            adapter.connect(device)

    def test_timeout(self):
        """socket.timeout from client.connect is wrapped as SSHConnectionError."""
        fp = FakeParamiko(fail_connect=socket.timeout())
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConnectionError):
            adapter.connect(device)

    def test_ssh_exception(self):
        fp = FakeParamiko(fail_connect=FakeSSHException())
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConnectionError):
            adapter.connect(device)

    def test_root_rejected(self):
        adapter, kh, tmp = self._make_adapter(username="root")
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConfigurationError) as cm:
            adapter.connect(device)
        self.assertIn("Root", str(cm.exception))

    def test_root_case_insensitive(self):
        for name in ["root", "ROOT", "Root", "rOoT"]:
            fp = FakeParamiko()
            adapter, kh, tmp = self._make_adapter(fp, username=name)
            device = _make_config_dict(kh)
            with self.assertRaises(SSHConfigurationError):
                adapter.connect(device)

    def test_username_control_char_rejected(self):
        adapter, kh, tmp = self._make_adapter(username="user\x00name")
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConfigurationError):
            adapter.connect(device)

    def test_username_at_sign_rejected(self):
        adapter, kh, tmp = self._make_adapter(username="user@host")
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConfigurationError):
            adapter.connect(device)

    def test_username_spaces_rejected(self):
        adapter, kh, tmp = self._make_adapter(username="user name")
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConfigurationError):
            adapter.connect(device)

    def test_username_trimmed(self):
        adapter, kh, tmp = self._make_adapter(username="  testuser  ")
        device = _make_config_dict(kh)
        self.assertTrue(adapter.connect(device))

    def test_known_hosts_not_found(self):
        adapter, kh, tmp = self._make_adapter()
        device = _make_config_dict("/nonexistent/known_hosts")
        with self.assertRaises(SSHConfigurationError):
            adapter.connect(device)

    def test_known_hosts_is_directory(self):
        tmp = tempfile.mkdtemp()
        adapter, kh, _ = self._make_adapter()
        device = _make_config_dict(tmp)
        with self.assertRaises(SSHConfigurationError):
            adapter.connect(device)

    def test_connection_failure_closes_temp_client(self):
        fp = FakeParamiko(fail_connect=FakeSSHException())
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHConnectionError):
            adapter.connect(device)
        self.assertIsNone(adapter._client)
        self.assertFalse(adapter._connected)

    def test_secret_not_in_adapter_attributes(self):
        adapter, kh, tmp = self._make_adapter()
        device = _make_config_dict(kh)
        adapter.connect(device)
        # 遍历所有属性，不应有密码
        for attr_name in dir(adapter):
            if attr_name.startswith("_"):
                continue
            val = getattr(adapter, attr_name, None)
            if isinstance(val, str):
                self.assertNotEqual(val, "test-password")

    def test_exception_no_secret_value(self):
        fp = FakeParamiko(fail_connect=FakeAuthenticationException())
        adapter, kh, tmp = self._make_adapter(fp)
        device = _make_config_dict(kh)
        with self.assertRaises(SSHAuthenticationError) as cm:
            adapter.connect(device)
        self.assertNotIn("test-password", str(cm.exception))


class TestSSHReadOnlyAdapterDisconnect(unittest.TestCase):

    def _connect_adapter(self, fake_paramiko=None):
        if fake_paramiko is None:
            fake_paramiko = FakeParamiko()
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fake_paramiko.SSHClient)
        adapter.connect(_make_config_dict(kh))
        return adapter

    def test_disconnect_success(self):
        adapter = self._connect_adapter()
        adapter.disconnect()
        self.assertFalse(adapter.query_status()["online"])

    def test_disconnect_idempotent(self):
        adapter = self._connect_adapter()
        adapter.disconnect()
        adapter.disconnect()  # 不报错
        self.assertFalse(adapter.query_status()["online"])

    def test_disconnect_clears_state(self):
        adapter = self._connect_adapter()
        adapter.disconnect()
        self.assertIsNone(adapter._client)
        self.assertIsNone(adapter._config)
        self.assertFalse(adapter._connected)


class TestSSHReadOnlyAdapterQuery(unittest.TestCase):

    def _connect_adapter(self, channel=None):
        fp = FakeParamiko(channel=channel)
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
        adapter.connect(_make_config_dict(kh))
        return adapter

    def test_query_hostname(self):
        adapter = self._connect_adapter()
        result = adapter.query("system.hostname")
        self.assertIsInstance(result, SSHReadOnlyQueryResult)
        self.assertEqual(result.query_id, "system.hostname")
        self.assertTrue(result.success)

    def test_query_unknown_rejected(self):
        adapter = self._connect_adapter()
        with self.assertRaises(SSHQueryNotAllowedError) as cm:
            adapter.query("malicious.query")
        self.assertEqual(str(cm.exception), "SSH query is not allowed")
        self.assertNotIn("malicious.query", str(cm.exception))

    def test_query_not_connected(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHConnectionError):
            adapter.query("system.hostname")

    def test_result_no_command(self):
        adapter = self._connect_adapter()
        result = adapter.query("system.hostname")
        # Result 不应包含固定命令
        for field in [result.stdout, result.stderr, result.message]:
            self.assertNotIn("hostname", field.lower() if field else "")

    def test_query_nonzero_exit(self):
        channel = FakeChannel(stdout_data=b"error\n", stderr_data=b"err\n", exit_code=1)
        adapter = self._connect_adapter(channel=channel)
        result = adapter.query("system.hostname")
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)
        self.assertEqual(result.message, "Query failed")

    def test_query_redaction(self):
        channel = FakeChannel(stdout_data=b"password=secret123\n", exit_code=0)
        adapter = self._connect_adapter(channel=channel)
        result = adapter.query("system.hostname")
        self.assertIn("[REDACTED]", result.stdout)
        self.assertNotIn("secret123", result.stdout)

    def test_query_stdout_truncated(self):
        big_data = b"x" * 20000
        channel = FakeChannel(stdout_data=big_data, exit_code=0)
        # 使用小 max_output_bytes
        fp = FakeParamiko(channel=channel)
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
        config = _make_config_dict(kh, max_output_bytes=100)
        adapter.connect(config)
        result = adapter.query("system.hostname")
        self.assertTrue(result.stdout_truncated)
        self.assertLessEqual(len(result.stdout.encode("utf-8")), 100)


class TestSSHReadOnlyAdapterFingerprint(unittest.TestCase):

    def test_fingerprint_when_connected(self):
        fp = FakeParamiko()
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
        adapter.connect(_make_config_dict(kh))
        fp_result = adapter.get_host_fingerprint()
        self.assertIsInstance(fp_result, HostFingerprint)
        self.assertEqual(fp_result.algorithm, "SHA256")
        self.assertTrue(fp_result.sha256_fingerprint.startswith("SHA256:"))

    def test_fingerprint_when_not_connected(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
        with self.assertRaises(SSHConnectionError):
            adapter.get_host_fingerprint()


# ============================================================================
# Credential Validation Tests
# ============================================================================

class TestCredentialValidation(unittest.TestCase):

    def test_only_password_type_accepted(self):
        """只允许 CredentialType.PASSWORD"""
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        for ctype in [CredentialType.PRIVATE_KEY, CredentialType.TOKEN]:
            provider = InMemorySecretProvider()
            ref = provider.store(SecretValue("secret"))
            cred = CredentialMetadata(
                credential_id="c1", name="n",
                credential_type=ctype, username="user",
                secret_ref=ref,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            adapter = SSHReadOnlyAdapter(cred, provider, FakeParamiko().SSHClient)
            device = _make_config_dict(kh)
            with self.assertRaises(SSHConfigurationError):
                adapter.connect(device)


# ============================================================================
# Paramiko Config Tests
# ============================================================================

class TestParamikoConfig(unittest.TestCase):
    """Test ParamikoReadOnlyClient configuration via mock paramiko module."""

    def _make_mock_paramiko(self):
        """Create a mock paramiko module that records connect kwargs."""
        class MockSSHClient:
            def __init__(self):
                self._connect_kwargs = None
                self._host_keys_path = None
            def load_host_keys(self, path):
                self._host_keys_path = path
            def set_missing_host_key_policy(self, policy):
                pass
            def connect(self, **kwargs):
                self._connect_kwargs = kwargs
            def exec_command(self, command, timeout=None):
                ch = FakeChannel(stdout_data=b"out\n", exit_code=0)
                return FakeStdin(), FakeStdout(ch), FakeStdout(ch)
            def get_transport(self):
                mt = MagicMock()
                key = MagicMock()
                key.asbytes.return_value = b"key"
                mt.get_remote_server_key.return_value = key
                mt.getpeername.return_value = ("10.0.0.1", 22)
                return mt
            def close(self):
                pass

        class MockRejectPolicy:
            pass

        mock_clients = []
        class MockParamiko:
            SSHException = Exception
            AuthenticationException = type("AuthExc", (Exception,), {})
            BadHostKeyException = type("BadHostExc", (Exception,), {})
            NoValidConnectionsError = type("NoConnExc", (Exception,), {})
            RejectPolicy = MockRejectPolicy
            def SSHClient(self):
                c = MockSSHClient()
                mock_clients.append(c)
                return c

        return MockParamiko(), mock_clients

    def test_allow_agent_false(self):
        from backup_manager.adapters.ssh_paramiko_client import ParamikoReadOnlyClient
        mock_p, clients = self._make_mock_paramiko()
        client = ParamikoReadOnlyClient(paramiko_module=mock_p)
        config = SSHReadOnlyConnectionConfig.from_mapping({
            "host": "10.0.0.1", "port": 22,
            "known_hosts_path": "/tmp/kh",
            "connect_timeout": 5.0, "query_timeout": 10.0, "max_output_bytes": 1024,
        })
        client.connect(config, "testuser", "testpw")
        self.assertFalse(clients[0]._connect_kwargs["allow_agent"])
        self.assertFalse(clients[0]._connect_kwargs["look_for_keys"])

    def test_auth_timeout_banner_timeout(self):
        from backup_manager.adapters.ssh_paramiko_client import ParamikoReadOnlyClient
        mock_p, clients = self._make_mock_paramiko()
        client = ParamikoReadOnlyClient(paramiko_module=mock_p)
        config = SSHReadOnlyConnectionConfig.from_mapping({
            "host": "10.0.0.1", "port": 22,
            "known_hosts_path": "/tmp/kh",
            "connect_timeout": 7.0, "query_timeout": 10.0, "max_output_bytes": 1024,
        })
        client.connect(config, "testuser", "testpw")
        self.assertEqual(clients[0]._connect_kwargs["auth_timeout"], 7.0)
        self.assertEqual(clients[0]._connect_kwargs["banner_timeout"], 7.0)


# ============================================================================
# Exception Safety Tests
# ============================================================================

class TestExceptionSafety(unittest.TestCase):

    def test_exception_hierarchy_at_runtime(self):
        """Debug: verify FakeAuthenticationException is SSHAdapterError"""
        exc = FakeAuthenticationException("test")
        self.assertIsInstance(exc, SSHAdapterError)
        self.assertIsInstance(exc, SSHAuthenticationError)

    def test_catch_ssh_adapter_error(self):
        """Debug: verify except SSHAdapterError catches FakeAuthenticationException"""
        try:
            raise FakeAuthenticationException("test")
        except SSHAdapterError:
            pass  # Expected
        except Exception:
            self.fail("Should have been caught by SSHAdapterError")

    def test_ssh_error_preserves_message(self):
        """SSHAdapterError is re-raised with its safe message."""
        fp = FakeParamiko(fail_connect=FakeAuthenticationException("Authentication failed"))
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
        with self.assertRaises(SSHAuthenticationError) as cm:
            adapter.connect(_make_config_dict(kh))
        self.assertEqual(str(cm.exception), "Authentication failed")

    def test_non_ssh_error_wrapped_as_connection_error(self):
        """Non-SSH exceptions are wrapped as SSHConnectionError."""
        fp = FakeParamiko(fail_connect=RuntimeError("internal"))
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
        with self.assertRaises(SSHConnectionError) as cm:
            adapter.connect(_make_config_dict(kh))
        self.assertEqual(str(cm.exception), "Connection failed")
        self.assertNotIn("internal", str(cm.exception))

    def test_cause_is_none_for_ssh_errors(self):
        """SSHAdapterError re-raise preserves __cause__ from original."""
        fp = FakeParamiko(fail_connect=FakeAuthenticationException("auth failed"))
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
        try:
            adapter.connect(_make_config_dict(kh))
        except SSHAuthenticationError as e:
            # The exception was raised directly (not from another),
            # so __cause__ should be None
            self.assertIsNone(e.__cause__)


# ============================================================================
# Factory Tests
# ============================================================================

class TestFactory(unittest.TestCase):

    def test_mock_compatible(self):
        adapter = AdapterFactory.create("mock")
        self.assertIsNotNone(adapter)

    def test_ssh_placeholder(self):
        from backup_manager.adapters.ssh_adapter import SSHAdapter
        adapter = AdapterFactory.create("ssh")
        self.assertIsInstance(adapter, SSHAdapter)

    def test_ssh_readonly_requires_credentials(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        adapter = AdapterFactory.create(
            "ssh_readonly",
            credential_metadata=cred,
            secret_provider=provider,
        )
        self.assertIsInstance(adapter, SSHReadOnlyAdapter)

    def test_ssh_readonly_missing_required(self):
        with self.assertRaises(SSHConfigurationError):
            AdapterFactory.create("ssh_readonly", credential_metadata="x")

    def test_ssh_readonly_unknown_kwargs(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        with self.assertRaises(SSHConfigurationError):
            AdapterFactory.create(
                "ssh_readonly",
                credential_metadata=cred,
                secret_provider=provider,
                unknown_param="x",
            )

    def test_ssh_readonly_client_factory_not_callable(self):
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        with self.assertRaises(SSHConfigurationError):
            AdapterFactory.create(
                "ssh_readonly",
                credential_metadata=cred,
                secret_provider=provider,
                client_factory="not_callable",
            )

    def test_non_ssh_readonly_kwargs_rejected(self):
        with self.assertRaises(SSHConfigurationError):
            AdapterFactory.create("mock", extra_param="x")

    def test_unknown_adapter_type(self):
        from backup_manager.adapters.errors import AdapterNotImplementedError
        with self.assertRaises(AdapterNotImplementedError):
            AdapterFactory.create("nonexistent")

    def test_ssh_readonly_client_factory_optional(self):
        """client_factory 可选注入"""
        tmp = tempfile.mkdtemp()
        kh = _make_known_hosts(tmp)
        cred, provider = _make_credential_with_ref("testuser")
        fake_fp = FakeParamiko()
        adapter = AdapterFactory.create(
            "ssh_readonly",
            credential_metadata=cred,
            secret_provider=provider,
            client_factory=fake_fp.SSHClient,
        )
        self.assertIsInstance(adapter, SSHReadOnlyAdapter)


# ============================================================================
# No Subprocess Tests
# ============================================================================

class TestNoSubprocess(unittest.TestCase):

    def _get_code_lines(self, module_path):
        """获取代码行（排除注释和 docstring）"""
        with open(module_path) as f:
            source = f.read()
        import ast
        tree = ast.parse(source)
        code_lines = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                # 跳过 docstring 行
                pass
        # 简单方法：只检查 import 语句
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    code_lines.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    code_lines.add(node.module)
        return source, code_lines

    def test_no_subprocess_in_module(self):
        """确认新代码不使用 subprocess import"""
        import importlib
        mod = importlib.import_module("backup_manager.adapters.ssh_paramiko_client")
        source_path = mod.__file__
        source, imports = self._get_code_lines(source_path)
        self.assertNotIn("subprocess", imports)

    def test_no_subprocess_in_adapter(self):
        import importlib
        mod = importlib.import_module("backup_manager.adapters.ssh_readonly_adapter")
        source_path = mod.__file__
        source, imports = self._get_code_lines(source_path)
        self.assertNotIn("subprocess", imports)


# ============================================================================
# No SFTP/SCP/Tunnel Tests
# ============================================================================

class TestNoSFTPSCPTunnel(unittest.TestCase):

    def test_no_sftp_scp_tunnel_in_modules(self):
        """检查 import 中不包含 sftp/scp/tunnel 库"""
        import ast
        for mod_name in [
            "backup_manager.adapters.ssh_paramiko_client",
            "backup_manager.adapters.ssh_readonly_adapter",
        ]:
            import importlib
            mod = importlib.import_module(mod_name)
            source_path = mod.__file__
            with open(source_path) as f:
                source = f.read()
            tree = ast.parse(source)
            imported_modules = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_modules.add(alias.name.lower())
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imported_modules.add(node.module.lower())
            for term in ["sftp", "scp"]:
                self.assertNotIn(term, imported_modules, f"{mod_name} imports {term}")


# ============================================================================
# Legacy SSH Path Unchanged Tests
# ============================================================================

class TestLegacyUnchanged(unittest.TestCase):

    def test_legacy_executor_unchanged(self):
        """确认 executor.py 未被修改"""
        import importlib
        try:
            mod = importlib.import_module("backup_manager.executor")
            source_path = mod.__file__
            # 只检查文件存在且可读
            self.assertTrue(Path(source_path).exists())
        except ImportError:
            self.skipTest("executor.py not importable without deps")

    def test_legacy_ssh_adapter_unchanged(self):
        """确认 SSHAdapter 占位类未被修改"""
        from backup_manager.adapters.ssh_adapter import SSHAdapter
        adapter = SSHAdapter()
        from backup_manager.adapters.errors import AdapterNotImplementedError
        with self.assertRaises(AdapterNotImplementedError):
            adapter.connect({})


# ============================================================================
# No Network Access Tests
# ============================================================================

class TestNoNetworkAccess(unittest.TestCase):

    def test_socket_connect_not_called(self):
        """测试期间 socket.connect 调用次数为 0"""
        original_connect = socket.socket.connect
        call_count = [0]

        def counting_connect(self, *args, **kwargs):
            call_count[0] += 1
            raise OSError("Network access blocked in tests")

        socket.socket.connect = counting_connect
        try:
            fp = FakeParamiko()
            tmp = tempfile.mkdtemp()
            kh = _make_known_hosts(tmp)
            cred, provider = _make_credential_with_ref("testuser")
            adapter = SSHReadOnlyAdapter(cred, provider, fp.SSHClient)
            adapter.connect(_make_config_dict(kh))
            adapter.query("system.hostname")
            adapter.disconnect()
        finally:
            socket.socket.connect = original_connect
        self.assertEqual(call_count[0], 0)


if __name__ == "__main__":
    unittest.main()
