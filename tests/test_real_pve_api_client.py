"""
WorkOps Real PVE API Client Tests
Sprint068: Real PVE API Client

覆盖：
- PVEConnectionConfig validation
- PVERuntimeState enum
- PVEAPIClient contract
- PVEReadOnlyExecutor contract
- RealPVEAPIConnector implementation
- validate_pve_readonly_operation
- Error model
- Security boundary
- Timeout validation
- SSL validation
"""

import unittest

from backup_manager.runtime.pve.connection import PVEConnectionConfig, PVERuntimeState
from backup_manager.runtime.pve.client import PVEAPIClient
from backup_manager.runtime.pve.readonly import (
    PVEReadOnlyExecutor,
    validate_pve_readonly_operation,
    ALLOWED_READONLY_OPERATIONS,
)
from backup_manager.runtime.pve.connector import RealPVEAPIConnector, PVEAPIConnector
from backup_manager.runtime.pve.exceptions import (
    PVEConnectionError,
    PVEAuthenticationError,
    PVEReadonlyViolationError,
    PVETimeoutError,
)
from backup_manager.runtime.pve.model import PVERuntimeMode, PVERuntimeSession
from backup_manager.runtime.pve.request import PVEAPIRequest
from backup_manager.runtime.pve.result import PVERuntimeResult
from backup_manager.runtime.pve.errors import (
    PVERuntimeError,
    InvalidPVERuntimeSessionError,
    PVEExecutionRejectedError,
    PVEConnectionUnavailableError,
)


# ============================================================================
# PVEConnectionConfig
# ============================================================================

class TestPVEConnectionConfig(unittest.TestCase):
    """PVE 连接配置测试"""

    def _make_config(self, **kwargs):
        defaults = {
            "host": "192.168.1.1",
            "port": 8006,
            "verify_ssl": True,
            "timeout_seconds": 30,
        }
        defaults.update(kwargs)
        return PVEConnectionConfig(**defaults)

    def test_valid_config(self):
        config = self._make_config()
        self.assertEqual(config.host, "192.168.1.1")
        self.assertEqual(config.port, 8006)
        self.assertTrue(config.verify_ssl)
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
        with self.assertRaises(PVEConnectionError):
            self._make_config(host="")

    def test_zero_port_rejected(self):
        with self.assertRaises(PVEConnectionError):
            self._make_config(port=0)

    def test_negative_port_rejected(self):
        with self.assertRaises(PVEConnectionError):
            self._make_config(port=-1)

    def test_invalid_verify_ssl_rejected(self):
        with self.assertRaises(PVEConnectionError):
            self._make_config(verify_ssl="yes")

    def test_zero_timeout_rejected(self):
        with self.assertRaises(PVEConnectionError):
            self._make_config(timeout_seconds=0)

    def test_negative_timeout_rejected(self):
        with self.assertRaises(PVEConnectionError):
            self._make_config(timeout_seconds=-1)

    def test_no_forbidden_fields(self):
        config = self._make_config()
        for attr in ["password", "secret", "token", "api_key", "credential", "private_key"]:
            self.assertFalse(hasattr(config, attr))

    def test_repr_no_secrets(self):
        config = self._make_config()
        r = repr(config)
        for term in ["password", "secret", "token", "api_key", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# PVERuntimeState
# ============================================================================

class TestPVERuntimeState(unittest.TestCase):
    """PVE 运行时状态测试"""

    def test_disconnected(self):
        self.assertEqual(PVERuntimeState.DISCONNECTED.value, "disconnected")

    def test_connecting(self):
        self.assertEqual(PVERuntimeState.CONNECTING.value, "connecting")

    def test_connected(self):
        self.assertEqual(PVERuntimeState.CONNECTED.value, "connected")

    def test_failed(self):
        self.assertEqual(PVERuntimeState.FAILED.value, "failed")

    def test_four_states(self):
        self.assertEqual(len(PVERuntimeState), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PVERuntimeState("nonexistent")


# ============================================================================
# PVEAPIClient Contract
# ============================================================================

class TestPVEAPIClientContract(unittest.TestCase):
    """PVE API 客户端契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEAPIClient, ABC))

    def test_has_connect(self):
        self.assertTrue(hasattr(PVEAPIClient, "connect"))

    def test_has_close(self):
        self.assertTrue(hasattr(PVEAPIClient, "close"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PVEAPIClient()

    def test_concrete_subclass(self):
        class MockClient(PVEAPIClient):
            def __init__(self):
                self.connected = False
            def connect(self, config):
                self.connected = True
            def close(self):
                self.connected = False
        client = MockClient()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        client.connect(config)
        self.assertTrue(client.connected)
        client.close()
        self.assertFalse(client.connected)

    def test_missing_connect(self):
        class BadClient(PVEAPIClient):
            def close(self):
                pass
        with self.assertRaises(TypeError):
            BadClient()

    def test_missing_close(self):
        class BadClient(PVEAPIClient):
            def connect(self, config):
                pass
        with self.assertRaises(TypeError):
            BadClient()


# ============================================================================
# PVEReadOnlyExecutor Contract
# ============================================================================

class TestPVEReadOnlyExecutorContract(unittest.TestCase):
    """PVE 只读执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEReadOnlyExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(PVEReadOnlyExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PVEReadOnlyExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(PVEReadOnlyExecutor):
            def execute(self, operation):
                return {"operation": operation, "status": "ok"}
        executor = MockExecutor()
        result = executor.execute("node_info")
        self.assertEqual(result["operation"], "node_info")

    def test_missing_execute(self):
        class BadExecutor(PVEReadOnlyExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# validate_pve_readonly_operation
# ============================================================================

class TestValidatePVEReadonlyOperation(unittest.TestCase):
    """验证 PVE 只读操作测试"""

    def test_valid_operations(self):
        for op in ALLOWED_READONLY_OPERATIONS:
            validate_pve_readonly_operation(op)

    def test_empty_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("")

    def test_create_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("create_vm")

    def test_delete_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("delete_vm")

    def test_update_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("update_config")

    def test_set_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("set_option")

    def test_modify_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("modify_vm")

    def test_execute_command_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("execute_command")

    def test_shell_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("shell")

    def test_sudo_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("sudo ls")

    def test_pipe_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("node_info | grep")

    def test_semicolon_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("node_info; rm -rf /")

    def test_redirect_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("echo > /etc/passwd")

    def test_allowed_operations_count(self):
        self.assertEqual(len(ALLOWED_READONLY_OPERATIONS), 3)


# ============================================================================
# RealPVEAPIConnector
# ============================================================================

class TestRealPVEAPIConnector(unittest.TestCase):
    """真实 PVE API 连接器测试"""

    def test_initial_state(self):
        connector = RealPVEAPIConnector()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_connect(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, PVERuntimeState.CONNECTED)

    def test_close(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_execute_readonly_connected(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("node_info")
        self.assertEqual(result["operation"], "node_info")

    def test_execute_readonly_not_connected(self):
        connector = RealPVEAPIConnector()
        with self.assertRaises(PVEConnectionError):
            connector.execute_readonly("node_info")

    def test_execute_readonly_forbidden_operation(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(PVEReadonlyViolationError):
            connector.execute_readonly("create_vm")

    def test_execute_readonly_shell_rejected(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(PVEReadonlyViolationError):
            connector.execute_readonly("shell")

    def test_connect_invalid_config(self):
        connector = RealPVEAPIConnector()
        with self.assertRaises(PVEConnectionError):
            connector.connect("not_a_config")

    def test_all_allowed_operations(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        for op in ALLOWED_READONLY_OPERATIONS:
            result = connector.execute_readonly(op)
            self.assertEqual(result["operation"], op)

    def test_close_idempotent(self):
        connector = RealPVEAPIConnector()
        connector.close()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_reconnect(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        connector.connect(config)
        self.assertEqual(connector.state, PVERuntimeState.CONNECTED)


# ============================================================================
# Error Model
# ============================================================================

class TestPVEExceptions(unittest.TestCase):
    """PVE 异常测试"""

    def test_connection_error(self):
        with self.assertRaises(PVEConnectionError):
            raise PVEConnectionError("test")

    def test_authentication_error(self):
        with self.assertRaises(PVEConnectionError):
            raise PVEAuthenticationError("test")

    def test_readonly_violation_error(self):
        with self.assertRaises(PVEConnectionError):
            raise PVEReadonlyViolationError("test")

    def test_timeout_error(self):
        with self.assertRaises(PVEConnectionError):
            raise PVETimeoutError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (PVEConnectionError, ("test",)),
            (PVEAuthenticationError, ("test",)),
            (PVEReadonlyViolationError, ("test",)),
            (PVETimeoutError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "api_key", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_config_no_credentials(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        for attr in ["password", "secret", "token", "api_key", "credential", "private_key"]:
            self.assertFalse(hasattr(config, attr))

    def test_no_subprocess(self):
        import ast
        import os
        pve_dir = os.path.join("backup_manager", "runtime", "pve")
        for filename in os.listdir(pve_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(pve_dir, filename)
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
        pve_dir = os.path.join("backup_manager", "runtime", "pve")
        for filename in os.listdir(pve_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(pve_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_connector_lifecycle(self):
        """完整连接器生命周期"""
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, PVERuntimeState.CONNECTED)
        result = connector.execute_readonly("node_info")
        self.assertEqual(result["operation"], "node_info")
        connector.close()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)


# ============================================================================
# Extended Tests
# ============================================================================

class TestRealPVEConnectorExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(PVEAuthenticationError, PVEConnectionError))
        self.assertTrue(issubclass(PVEReadonlyViolationError, PVEConnectionError))
        self.assertTrue(issubclass(PVETimeoutError, PVEConnectionError))

    def test_config_preserves_all_fields(self):
        config = PVEConnectionConfig(
            host="pve.local", port=8006,
            verify_ssl=False, timeout_seconds=60,
        )
        self.assertEqual(config.host, "pve.local")
        self.assertEqual(config.port, 8006)
        self.assertFalse(config.verify_ssl)
        self.assertEqual(config.timeout_seconds, 60)

    def test_config_repr_no_secrets(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        r = repr(config)
        for term in ["password", "secret", "token", "api_key", "private_key"]:
            self.assertNotIn(term, r.lower())

    def test_config_no_password(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "password"))

    def test_config_no_secret(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "secret"))

    def test_config_no_token(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "token"))

    def test_config_no_api_key(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "api_key"))

    def test_config_no_private_key(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "private_key"))

    def test_config_no_credential(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "credential"))

    def test_config_whitespace_host_rejected(self):
        with self.assertRaises(PVEConnectionError):
            PVEConnectionConfig(
                host="   ", port=8006,
                verify_ssl=True, timeout_seconds=30,
            )

    def test_config_large_port(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=65535,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.port, 65535)

    def test_config_large_timeout(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=3600,
        )
        self.assertEqual(config.timeout_seconds, 3600)

    def test_config_ssl_false(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=False, timeout_seconds=30,
        )
        self.assertFalse(config.verify_ssl)

    def test_state_all_values(self):
        for state in PVERuntimeState:
            self.assertIsInstance(state.value, str)

    def test_connector_state_property(self):
        connector = RealPVEAPIConnector()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_connector_connect_then_state(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, PVERuntimeState.CONNECTED)

    def test_connector_close_then_state(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_connector_execute_vm_status(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("vm_status")
        self.assertEqual(result["operation"], "vm_status")

    def test_connector_execute_storage_status(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("storage_status")
        self.assertEqual(result["operation"], "storage_status")

    def test_connector_execute_delete_rejected(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(PVEReadonlyViolationError):
            connector.execute_readonly("delete_vm")

    def test_connector_execute_update_rejected(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(PVEReadonlyViolationError):
            connector.execute_readonly("update_config")

    def test_connector_not_connected_execute(self):
        connector = RealPVEAPIConnector()
        with self.assertRaises(PVEConnectionError):
            connector.execute_readonly("node_info")

    def test_connector_double_close(self):
        connector = RealPVEAPIConnector()
        connector.close()
        connector.close()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_connector_reconnect_execute(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        connector.connect(config)
        result = connector.execute_readonly("node_info")
        self.assertEqual(result["operation"], "node_info")

    def test_error_messages_safe(self):
        try:
            raise PVEConnectionError("test")
        except PVEConnectionError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "api_key", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_auth_error_message(self):
        exc = PVEAuthenticationError("auth failed")
        self.assertIn("auth failed", str(exc))

    def test_timeout_error_message(self):
        exc = PVETimeoutError("timeout")
        self.assertIn("timeout", str(exc))

    def test_readonly_violation_message(self):
        exc = PVEReadonlyViolationError("forbidden")
        self.assertIn("forbidden", str(exc))

    def test_connector_result_has_status(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("node_info")
        self.assertIn("status", result)

    def test_connector_result_has_message(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("node_info")
        self.assertIn("message", result)

    def test_connector_result_contract_only(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("node_info")
        self.assertEqual(result["status"], "contract_only")

    def test_allowed_operations_frozenset(self):
        self.assertIsInstance(ALLOWED_READONLY_OPERATIONS, frozenset)

    def test_validate_operation_type_check(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation(123)

    def test_client_connect_close_lifecycle(self):
        class MockClient(PVEAPIClient):
            def __init__(self):
                self.connected = False
            def connect(self, config):
                self.connected = True
            def close(self):
                self.connected = False
        client = MockClient()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        client.connect(config)
        self.assertTrue(client.connected)
        client.close()
        self.assertFalse(client.connected)

    def test_executor_returns_dict(self):
        class MockExecutor(PVEReadOnlyExecutor):
            def execute(self, operation):
                return {"operation": operation, "status": "ok"}
        executor = MockExecutor()
        result = executor.execute("node_info")
        self.assertIsInstance(result, dict)

    def test_config_no_command(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "command"))

    def test_exception_hierarchy_pve_runtime(self):
        self.assertTrue(issubclass(PVEConnectionError, Exception))
        self.assertTrue(issubclass(PVEAuthenticationError, PVEConnectionError))
        self.assertTrue(issubclass(PVEReadonlyViolationError, PVEConnectionError))
        self.assertTrue(issubclass(PVETimeoutError, PVEConnectionError))

    def test_config_hostname(self):
        config = PVEConnectionConfig(
            host="pve.example.com", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.host, "pve.example.com")

    def test_config_ipv6(self):
        config = PVEConnectionConfig(
            host="::1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.host, "::1")

    def test_config_port_1(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=1,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.port, 1)

    def test_config_timeout_1(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=1,
        )
        self.assertEqual(config.timeout_seconds, 1)

    def test_connector_status_transitions(self):
        connector = RealPVEAPIConnector()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, PVERuntimeState.CONNECTED)
        connector.close()
        self.assertEqual(connector.state, PVERuntimeState.DISCONNECTED)

    def test_connector_multiple_configs(self):
        connector = RealPVEAPIConnector()
        for host in ["192.168.1.1", "10.0.0.1", "pve.local"]:
            config = PVEConnectionConfig(
                host=host, port=8006,
                verify_ssl=True, timeout_seconds=30,
            )
            connector.connect(config)
            self.assertEqual(connector.state, PVERuntimeState.CONNECTED)
            connector.close()

    def test_connector_execute_all_allowed(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        for op in ["node_info", "vm_status", "storage_status"]:
            result = connector.execute_readonly(op)
            self.assertEqual(result["operation"], op)

    def test_config_no_command(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "command"))

    def test_config_no_ssh(self):
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "ssh"))

    def test_validate_modify_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("modify_vm")

    def test_validate_execute_command_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("execute_command")

    def test_validate_backtick_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("`id`")

    def test_validate_dollar_paren_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("$(id)")

    def test_validate_chmod_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("chmod 777 /tmp")

    def test_validate_dd_rejected(self):
        with self.assertRaises(PVEReadonlyViolationError):
            validate_pve_readonly_operation("dd if=/dev/zero of=/tmp/test")

    def test_state_disconnected_value(self):
        self.assertEqual(PVERuntimeState.DISCONNECTED.value, "disconnected")

    def test_state_connecting_value(self):
        self.assertEqual(PVERuntimeState.CONNECTING.value, "connecting")

    def test_state_connected_value(self):
        self.assertEqual(PVERuntimeState.CONNECTED.value, "connected")

    def test_state_failed_value(self):
        self.assertEqual(PVERuntimeState.FAILED.value, "failed")

    def test_connector_result_returns_dict(self):
        connector = RealPVEAPIConnector()
        config = PVEConnectionConfig(
            host="192.168.1.1", port=8006,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("node_info")
        self.assertIsInstance(result, dict)

    def test_pve_api_connector_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEAPIConnector, ABC))


if __name__ == "__main__":
    unittest.main()
