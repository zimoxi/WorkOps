"""
WorkOps Real Linux SSH Connector Tests
Sprint067: Real Linux SSH Connector

覆盖：
- SSHConnectionConfig validation
- SSHConnectionState enum
- SSHClient contract
- ReadOnlySSHExecutor contract
- RealLinuxSSHConnector implementation
- validate_readonly_operation
- Error model
- Security boundary
- Timeout validation
"""

import unittest
from datetime import datetime, timezone

from backup_manager.runtime.ssh.connection import SSHConnectionConfig, SSHConnectionState
from backup_manager.runtime.ssh.client import SSHClient
from backup_manager.runtime.ssh.readonly import (
    ReadOnlySSHExecutor,
    validate_readonly_operation,
    ALLOWED_READONLY_OPERATIONS,
)
from backup_manager.runtime.ssh.connector import RealLinuxSSHConnector, LinuxSSHConnector
from backup_manager.runtime.ssh.exceptions import (
    SSHConnectionError,
    SSHAuthenticationError,
    SSHReadonlyViolationError,
    SSHTimeoutError,
)
from backup_manager.runtime.ssh.model import SSHSessionMode, SSHSession
from backup_manager.runtime.ssh.session import SSHExecutionRequest
from backup_manager.runtime.ssh.result import SSHRuntimeResult
from backup_manager.runtime.ssh.errors import (
    SSHRuntimeError,
    InvalidSSHSessionError,
    SSHExecutionRejectedError,
    SSHConnectionUnavailableError,
)


# ============================================================================
# SSHConnectionConfig
# ============================================================================

class TestSSHConnectionConfig(unittest.TestCase):
    """SSH 连接配置测试"""

    def _make_config(self, **kwargs):
        defaults = {
            "host": "192.168.1.1",
            "port": 22,
            "username": "admin",
            "timeout_seconds": 30,
        }
        defaults.update(kwargs)
        return SSHConnectionConfig(**defaults)

    def test_valid_config(self):
        config = self._make_config()
        self.assertEqual(config.host, "192.168.1.1")
        self.assertEqual(config.port, 22)
        self.assertEqual(config.username, "admin")
        self.assertEqual(config.timeout_seconds, 30)

    def test_frozen(self):
        config = self._make_config()
        with self.assertRaises(AttributeError):
            config.host = "other"

    def test_slots(self):
        config = self._make_config()
        with self.assertRaises(AttributeError):
            config.__dict__

    def test_empty_host_rejected(self):
        with self.assertRaises(SSHConnectionError):
            self._make_config(host="")

    def test_zero_port_rejected(self):
        with self.assertRaises(SSHConnectionError):
            self._make_config(port=0)

    def test_negative_port_rejected(self):
        with self.assertRaises(SSHConnectionError):
            self._make_config(port=-1)

    def test_empty_username_rejected(self):
        with self.assertRaises(SSHConnectionError):
            self._make_config(username="")

    def test_zero_timeout_rejected(self):
        with self.assertRaises(SSHConnectionError):
            self._make_config(timeout_seconds=0)

    def test_negative_timeout_rejected(self):
        with self.assertRaises(SSHConnectionError):
            self._make_config(timeout_seconds=-1)

    def test_no_forbidden_fields(self):
        config = self._make_config()
        for attr in ["password", "secret", "token", "private_key", "credential"]:
            self.assertFalse(hasattr(config, attr))

    def test_repr_no_secrets(self):
        config = self._make_config()
        r = repr(config)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# SSHConnectionState
# ============================================================================

class TestSSHConnectionState(unittest.TestCase):
    """SSH 连接状态测试"""

    def test_disconnected(self):
        self.assertEqual(SSHConnectionState.DISCONNECTED.value, "disconnected")

    def test_connecting(self):
        self.assertEqual(SSHConnectionState.CONNECTING.value, "connecting")

    def test_connected(self):
        self.assertEqual(SSHConnectionState.CONNECTED.value, "connected")

    def test_failed(self):
        self.assertEqual(SSHConnectionState.FAILED.value, "failed")

    def test_four_states(self):
        self.assertEqual(len(SSHConnectionState), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            SSHConnectionState("nonexistent")


# ============================================================================
# SSHClient Contract
# ============================================================================

class TestSSHClientContract(unittest.TestCase):
    """SSH 客户端契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(SSHClient, ABC))

    def test_has_connect(self):
        self.assertTrue(hasattr(SSHClient, "connect"))

    def test_has_close(self):
        self.assertTrue(hasattr(SSHClient, "close"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            SSHClient()

    def test_concrete_subclass(self):
        class MockClient(SSHClient):
            def __init__(self):
                self.connected = False
            def connect(self, config):
                self.connected = True
            def close(self):
                self.connected = False
        client = MockClient()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        client.connect(config)
        self.assertTrue(client.connected)
        client.close()
        self.assertFalse(client.connected)

    def test_missing_connect(self):
        class BadClient(SSHClient):
            def close(self):
                pass
        with self.assertRaises(TypeError):
            BadClient()

    def test_missing_close(self):
        class BadClient(SSHClient):
            def connect(self, config):
                pass
        with self.assertRaises(TypeError):
            BadClient()


# ============================================================================
# ReadOnlySSHExecutor Contract
# ============================================================================

class TestReadOnlySSHExecutorContract(unittest.TestCase):
    """只读 SSH 执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(ReadOnlySSHExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(ReadOnlySSHExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ReadOnlySSHExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(ReadOnlySSHExecutor):
            def execute(self, operation):
                return {"operation": operation, "status": "ok"}
        executor = MockExecutor()
        result = executor.execute("system_info")
        self.assertEqual(result["operation"], "system_info")

    def test_missing_execute(self):
        class BadExecutor(ReadOnlySSHExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# validate_readonly_operation
# ============================================================================

class TestValidateReadonlyOperation(unittest.TestCase):
    """验证只读操作测试"""

    def test_valid_operations(self):
        for op in ALLOWED_READONLY_OPERATIONS:
            validate_readonly_operation(op)

    def test_empty_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("")

    def test_shell_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("shell")

    def test_sudo_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("sudo ls")

    def test_script_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("script")

    def test_rm_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("rm -rf /")

    def test_pipe_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("cat | grep")

    def test_semicolon_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("ls; rm -rf /")

    def test_redirect_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("echo > /etc/passwd")

    def test_backtick_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("`whoami`")

    def test_dollar_paren_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("$(whoami)")

    def test_chmod_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("chmod 777 /")

    def test_chown_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("chown root /")

    def test_mkfs_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("mkfs.ext4 /dev/sda")

    def test_dd_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("dd if=/dev/zero of=/dev/sda")

    def test_allowed_operations_count(self):
        self.assertEqual(len(ALLOWED_READONLY_OPERATIONS), 3)


# ============================================================================
# RealLinuxSSHConnector
# ============================================================================

class TestRealLinuxSSHConnector(unittest.TestCase):
    """真实 Linux SSH 连接器测试"""

    def test_initial_state(self):
        connector = RealLinuxSSHConnector()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_connect(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, SSHConnectionState.CONNECTED)

    def test_close(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_execute_readonly_connected(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["operation"], "system_info")

    def test_execute_readonly_not_connected(self):
        connector = RealLinuxSSHConnector()
        with self.assertRaises(SSHConnectionError):
            connector.execute_readonly("system_info")

    def test_execute_readonly_forbidden_operation(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(SSHReadonlyViolationError):
            connector.execute_readonly("sudo ls")

    def test_execute_readonly_shell_rejected(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(SSHReadonlyViolationError):
            connector.execute_readonly("shell")

    def test_connect_invalid_config(self):
        connector = RealLinuxSSHConnector()
        with self.assertRaises(SSHConnectionError):
            connector.connect("not_a_config")

    def test_all_allowed_operations(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        for op in ALLOWED_READONLY_OPERATIONS:
            result = connector.execute_readonly(op)
            self.assertEqual(result["operation"], op)

    def test_close_idempotent(self):
        connector = RealLinuxSSHConnector()
        connector.close()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_reconnect(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        connector.connect(config)
        self.assertEqual(connector.state, SSHConnectionState.CONNECTED)


# ============================================================================
# Error Model
# ============================================================================

class TestSSHExceptions(unittest.TestCase):
    """SSH 异常测试"""

    def test_connection_error(self):
        with self.assertRaises(SSHConnectionError):
            raise SSHConnectionError("test")

    def test_authentication_error(self):
        with self.assertRaises(SSHConnectionError):
            raise SSHAuthenticationError("test")

    def test_readonly_violation_error(self):
        with self.assertRaises(SSHConnectionError):
            raise SSHReadonlyViolationError("test")

    def test_timeout_error(self):
        with self.assertRaises(SSHConnectionError):
            raise SSHTimeoutError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (SSHConnectionError, ("test",)),
            (SSHAuthenticationError, ("test",)),
            (SSHReadonlyViolationError, ("test",)),
            (SSHTimeoutError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_config_no_credentials(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        for attr in ["password", "secret", "token", "private_key", "credential"]:
            self.assertFalse(hasattr(config, attr))

    def test_no_subprocess(self):
        import ast
        import os
        ssh_dir = os.path.join("backup_manager", "runtime", "ssh")
        for filename in os.listdir(ssh_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(ssh_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                        self.assertNotEqual(alias.name, "os")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if "subprocess" in node.module:
                            self.fail(f"subprocess imported in {filename}")
                        if node.module == "os" and any(
                            a.name in ("system", "popen") for a in node.names
                        ):
                            self.fail(f"os.system imported in {filename}")

    def test_no_exec_eval(self):
        import ast
        import os
        ssh_dir = os.path.join("backup_manager", "runtime", "ssh")
        for filename in os.listdir(ssh_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(ssh_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_connector_lifecycle(self):
        """完整连接器生命周期"""
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, SSHConnectionState.CONNECTED)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["operation"], "system_info")
        connector.close()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)


# ============================================================================
# Extended Tests
# ============================================================================

class TestRealSSHConnectorExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(SSHAuthenticationError, SSHConnectionError))
        self.assertTrue(issubclass(SSHReadonlyViolationError, SSHConnectionError))
        self.assertTrue(issubclass(SSHTimeoutError, SSHConnectionError))

    def test_config_preserves_all_fields(self):
        config = SSHConnectionConfig(
            host="10.0.0.1", port=2222,
            username="root", timeout_seconds=60,
        )
        self.assertEqual(config.host, "10.0.0.1")
        self.assertEqual(config.port, 2222)
        self.assertEqual(config.username, "root")
        self.assertEqual(config.timeout_seconds, 60)

    def test_config_repr_no_secrets(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        r = repr(config)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())

    def test_config_no_password(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "password"))

    def test_config_no_secret(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "secret"))

    def test_config_no_token(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "token"))

    def test_config_no_private_key(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "private_key"))

    def test_config_no_credential(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "credential"))

    def test_config_whitespace_host_rejected(self):
        with self.assertRaises(SSHConnectionError):
            SSHConnectionConfig(
                host="   ", port=22,
                username="admin", timeout_seconds=30,
            )

    def test_config_whitespace_username_rejected(self):
        with self.assertRaises(SSHConnectionError):
            SSHConnectionConfig(
                host="192.168.1.1", port=22,
                username="   ", timeout_seconds=30,
            )

    def test_config_large_port(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=65535,
            username="admin", timeout_seconds=30,
        )
        self.assertEqual(config.port, 65535)

    def test_config_large_timeout(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=3600,
        )
        self.assertEqual(config.timeout_seconds, 3600)

    def test_state_all_values(self):
        for state in SSHConnectionState:
            self.assertIsInstance(state.value, str)

    def test_connector_state_property(self):
        connector = RealLinuxSSHConnector()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_connector_connect_then_state(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, SSHConnectionState.CONNECTED)

    def test_connector_close_then_state(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_connector_execute_disk_info(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("disk_info")
        self.assertEqual(result["operation"], "disk_info")

    def test_connector_execute_service_status(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("service_status")
        self.assertEqual(result["operation"], "service_status")

    def test_connector_execute_pipe_rejected(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(SSHReadonlyViolationError):
            connector.execute_readonly("ls | grep foo")

    def test_connector_execute_semicolon_rejected(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(SSHReadonlyViolationError):
            connector.execute_readonly("ls; rm -rf /")

    def test_connector_execute_redirect_rejected(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(SSHReadonlyViolationError):
            connector.execute_readonly("echo > /etc/passwd")

    def test_connector_not_connected_execute(self):
        connector = RealLinuxSSHConnector()
        with self.assertRaises(SSHConnectionError):
            connector.execute_readonly("system_info")

    def test_connector_double_close(self):
        connector = RealLinuxSSHConnector()
        connector.close()
        connector.close()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_connector_reconnect_execute(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["operation"], "system_info")

    def test_error_messages_safe(self):
        try:
            raise SSHConnectionError("test")
        except SSHConnectionError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_auth_error_message(self):
        exc = SSHAuthenticationError("auth failed")
        self.assertIn("auth failed", str(exc))

    def test_timeout_error_message(self):
        exc = SSHTimeoutError("timeout")
        self.assertIn("timeout", str(exc))

    def test_readonly_violation_message(self):
        exc = SSHReadonlyViolationError("forbidden")
        self.assertIn("forbidden", str(exc))

    def test_client_connect_close_lifecycle(self):
        class MockClient(SSHClient):
            def __init__(self):
                self.connected = False
            def connect(self, config):
                self.connected = True
            def close(self):
                self.connected = False
        client = MockClient()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        client.connect(config)
        self.assertTrue(client.connected)
        client.close()
        self.assertFalse(client.connected)

    def test_executor_returns_dict(self):
        class MockExecutor(ReadOnlySSHExecutor):
            def execute(self, operation):
                return {"operation": operation, "status": "ok"}
        executor = MockExecutor()
        result = executor.execute("system_info")
        self.assertIsInstance(result, dict)

    def test_validate_operation_type_check(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation(123)

    def test_config_hostname(self):
        config = SSHConnectionConfig(
            host="myhost.example.com", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertEqual(config.host, "myhost.example.com")

    def test_config_ipv6(self):
        config = SSHConnectionConfig(
            host="::1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertEqual(config.host, "::1")

    def test_config_port_1(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=1,
            username="admin", timeout_seconds=30,
        )
        self.assertEqual(config.port, 1)

    def test_config_timeout_1(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=1,
        )
        self.assertEqual(config.timeout_seconds, 1)

    def test_connector_status_transitions(self):
        connector = RealLinuxSSHConnector()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, SSHConnectionState.CONNECTED)
        connector.close()
        self.assertEqual(connector.state, SSHConnectionState.DISCONNECTED)

    def test_connector_result_has_status(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertIn("status", result)

    def test_connector_result_has_message(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertIn("message", result)

    def test_validate_backtick_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("`id`")

    def test_validate_dollar_paren_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("$(id)")

    def test_validate_chmod_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("chmod 777 /tmp")

    def test_validate_chown_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("chown root /tmp")

    def test_validate_mkfs_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("mkfs.ext4 /dev/sdb")

    def test_validate_dd_rejected(self):
        with self.assertRaises(SSHReadonlyViolationError):
            validate_readonly_operation("dd if=/dev/zero of=/tmp/test bs=1M count=1")

    def test_state_disconnected_value(self):
        self.assertEqual(SSHConnectionState.DISCONNECTED.value, "disconnected")

    def test_state_connecting_value(self):
        self.assertEqual(SSHConnectionState.CONNECTING.value, "connecting")

    def test_state_connected_value(self):
        self.assertEqual(SSHConnectionState.CONNECTED.value, "connected")

    def test_state_failed_value(self):
        self.assertEqual(SSHConnectionState.FAILED.value, "failed")

    def test_connector_multiple_configs(self):
        connector = RealLinuxSSHConnector()
        for host in ["192.168.1.1", "10.0.0.1", "myhost.local"]:
            config = SSHConnectionConfig(
                host=host, port=22,
                username="admin", timeout_seconds=30,
            )
            connector.connect(config)
            self.assertEqual(connector.state, SSHConnectionState.CONNECTED)
            connector.close()

    def test_connector_execute_all_allowed(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        for op in ["system_info", "disk_info", "service_status"]:
            result = connector.execute_readonly(op)
            self.assertEqual(result["operation"], op)

    def test_exception_hierarchy_ssh_runtime(self):
        self.assertTrue(issubclass(SSHConnectionError, Exception))
        self.assertTrue(issubclass(SSHAuthenticationError, SSHConnectionError))
        self.assertTrue(issubclass(SSHReadonlyViolationError, SSHConnectionError))
        self.assertTrue(issubclass(SSHTimeoutError, SSHConnectionError))

    def test_config_no_command(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "command"))

    def test_config_no_ssh(self):
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "ssh"))

    def test_connector_result_contract_only(self):
        connector = RealLinuxSSHConnector()
        config = SSHConnectionConfig(
            host="192.168.1.1", port=22,
            username="admin", timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["status"], "contract_only")

    def test_allowed_operations_frozenset(self):
        self.assertIsInstance(ALLOWED_READONLY_OPERATIONS, frozenset)


if __name__ == "__main__":
    unittest.main()
