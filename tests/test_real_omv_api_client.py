"""
WorkOps Real OMV API Client Tests
Sprint069: Real OMV API Client

覆盖：
- OMVConnectionConfig validation
- OMVRuntimeState enum
- OMVAPIClient contract
- OMVReadOnlyExecutor contract
- RealOMVAPIConnector implementation
- validate_omv_readonly_operation
- Error model
- Security boundary
- Timeout validation
- SSL validation
"""

import unittest

from backup_manager.runtime.omv.connection import OMVConnectionConfig, OMVRuntimeState
from backup_manager.runtime.omv.client import OMVAPIClient
from backup_manager.runtime.omv.readonly import (
    OMVReadOnlyExecutor,
    validate_omv_readonly_operation,
    ALLOWED_READONLY_OPERATIONS,
)
from backup_manager.runtime.omv.connector import RealOMVAPIConnector, OMVAPIConnector
from backup_manager.runtime.omv.exceptions import (
    OMVConnectionError,
    OMVAuthenticationError,
    OMVReadonlyViolationError,
    OMVTimeoutError,
)
from backup_manager.runtime.omv.model import OMVRuntimeMode, OMVRuntimeSession
from backup_manager.runtime.omv.request import OMVAPIRequest
from backup_manager.runtime.omv.result import OMVRuntimeResult
from backup_manager.runtime.omv.errors import (
    OMVRuntimeError,
    InvalidOMVRuntimeSessionError,
    OMVExecutionRejectedError,
    OMVConnectionUnavailableError,
)


# ============================================================================
# OMVConnectionConfig
# ============================================================================

class TestOMVConnectionConfig(unittest.TestCase):
    """OMV 连接配置测试"""

    def _make_config(self, **kwargs):
        defaults = {
            "host": "192.168.1.1",
            "port": 80,
            "verify_ssl": True,
            "timeout_seconds": 30,
        }
        defaults.update(kwargs)
        return OMVConnectionConfig(**defaults)

    def test_valid_config(self):
        config = self._make_config()
        self.assertEqual(config.host, "192.168.1.1")
        self.assertEqual(config.port, 80)
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
        with self.assertRaises(OMVConnectionError):
            self._make_config(host="")

    def test_zero_port_rejected(self):
        with self.assertRaises(OMVConnectionError):
            self._make_config(port=0)

    def test_negative_port_rejected(self):
        with self.assertRaises(OMVConnectionError):
            self._make_config(port=-1)

    def test_invalid_verify_ssl_rejected(self):
        with self.assertRaises(OMVConnectionError):
            self._make_config(verify_ssl="yes")

    def test_zero_timeout_rejected(self):
        with self.assertRaises(OMVConnectionError):
            self._make_config(timeout_seconds=0)

    def test_negative_timeout_rejected(self):
        with self.assertRaises(OMVConnectionError):
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
# OMVRuntimeState
# ============================================================================

class TestOMVRuntimeState(unittest.TestCase):
    """OMV 运行时状态测试"""

    def test_disconnected(self):
        self.assertEqual(OMVRuntimeState.DISCONNECTED.value, "disconnected")

    def test_connecting(self):
        self.assertEqual(OMVRuntimeState.CONNECTING.value, "connecting")

    def test_connected(self):
        self.assertEqual(OMVRuntimeState.CONNECTED.value, "connected")

    def test_failed(self):
        self.assertEqual(OMVRuntimeState.FAILED.value, "failed")

    def test_four_states(self):
        self.assertEqual(len(OMVRuntimeState), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            OMVRuntimeState("nonexistent")


# ============================================================================
# OMVAPIClient Contract
# ============================================================================

class TestOMVAPIClientContract(unittest.TestCase):
    """OMV API 客户端契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVAPIClient, ABC))

    def test_has_connect(self):
        self.assertTrue(hasattr(OMVAPIClient, "connect"))

    def test_has_close(self):
        self.assertTrue(hasattr(OMVAPIClient, "close"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OMVAPIClient()

    def test_concrete_subclass(self):
        class MockClient(OMVAPIClient):
            def __init__(self):
                self.connected = False
            def connect(self, config):
                self.connected = True
            def close(self):
                self.connected = False
        client = MockClient()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        client.connect(config)
        self.assertTrue(client.connected)
        client.close()
        self.assertFalse(client.connected)

    def test_missing_connect(self):
        class BadClient(OMVAPIClient):
            def close(self):
                pass
        with self.assertRaises(TypeError):
            BadClient()

    def test_missing_close(self):
        class BadClient(OMVAPIClient):
            def connect(self, config):
                pass
        with self.assertRaises(TypeError):
            BadClient()


# ============================================================================
# OMVReadOnlyExecutor Contract
# ============================================================================

class TestOMVReadOnlyExecutorContract(unittest.TestCase):
    """OMV 只读执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVReadOnlyExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(OMVReadOnlyExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OMVReadOnlyExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(OMVReadOnlyExecutor):
            def execute(self, operation):
                return {"operation": operation, "status": "ok"}
        executor = MockExecutor()
        result = executor.execute("system_info")
        self.assertEqual(result["operation"], "system_info")

    def test_missing_execute(self):
        class BadExecutor(OMVReadOnlyExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# validate_omv_readonly_operation
# ============================================================================

class TestValidateOMVReadonlyOperation(unittest.TestCase):
    """验证 OMV 只读操作测试"""

    def test_valid_operations(self):
        for op in ALLOWED_READONLY_OPERATIONS:
            validate_omv_readonly_operation(op)

    def test_empty_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("")

    def test_create_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("create_share")

    def test_delete_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("delete_share")

    def test_update_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("update_config")

    def test_set_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("set_option")

    def test_modify_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("modify_share")

    def test_write_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("write_file")

    def test_upload_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("upload_file")

    def test_shell_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("shell")

    def test_sudo_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("sudo ls")

    def test_pipe_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("system_info | grep")

    def test_semicolon_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("system_info; rm -rf /")

    def test_redirect_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("echo > /etc/passwd")

    def test_allowed_operations_count(self):
        self.assertEqual(len(ALLOWED_READONLY_OPERATIONS), 3)


# ============================================================================
# RealOMVAPIConnector
# ============================================================================

class TestRealOMVAPIConnector(unittest.TestCase):
    """真实 OMV API 连接器测试"""

    def test_initial_state(self):
        connector = RealOMVAPIConnector()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_connect(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, OMVRuntimeState.CONNECTED)

    def test_close(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_execute_readonly_connected(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["operation"], "system_info")

    def test_execute_readonly_not_connected(self):
        connector = RealOMVAPIConnector()
        with self.assertRaises(OMVConnectionError):
            connector.execute_readonly("system_info")

    def test_execute_readonly_forbidden_operation(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(OMVReadonlyViolationError):
            connector.execute_readonly("create_share")

    def test_execute_readonly_shell_rejected(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(OMVReadonlyViolationError):
            connector.execute_readonly("shell")

    def test_connect_invalid_config(self):
        connector = RealOMVAPIConnector()
        with self.assertRaises(OMVConnectionError):
            connector.connect("not_a_config")

    def test_all_allowed_operations(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        for op in ALLOWED_READONLY_OPERATIONS:
            result = connector.execute_readonly(op)
            self.assertEqual(result["operation"], op)

    def test_close_idempotent(self):
        connector = RealOMVAPIConnector()
        connector.close()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_reconnect(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        connector.connect(config)
        self.assertEqual(connector.state, OMVRuntimeState.CONNECTED)


# ============================================================================
# Error Model
# ============================================================================

class TestOMVExceptions(unittest.TestCase):
    """OMV 异常测试"""

    def test_connection_error(self):
        with self.assertRaises(OMVConnectionError):
            raise OMVConnectionError("test")

    def test_authentication_error(self):
        with self.assertRaises(OMVConnectionError):
            raise OMVAuthenticationError("test")

    def test_readonly_violation_error(self):
        with self.assertRaises(OMVConnectionError):
            raise OMVReadonlyViolationError("test")

    def test_timeout_error(self):
        with self.assertRaises(OMVConnectionError):
            raise OMVTimeoutError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (OMVConnectionError, ("test",)),
            (OMVAuthenticationError, ("test",)),
            (OMVReadonlyViolationError, ("test",)),
            (OMVTimeoutError, ("test",)),
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
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        for attr in ["password", "secret", "token", "api_key", "credential", "private_key"]:
            self.assertFalse(hasattr(config, attr))

    def test_no_subprocess(self):
        import ast
        import os
        omv_dir = os.path.join("backup_manager", "runtime", "omv")
        for filename in os.listdir(omv_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(omv_dir, filename)
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
        omv_dir = os.path.join("backup_manager", "runtime", "omv")
        for filename in os.listdir(omv_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(omv_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_connector_lifecycle(self):
        """完整连接器生命周期"""
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, OMVRuntimeState.CONNECTED)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["operation"], "system_info")
        connector.close()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)


# ============================================================================
# Extended Tests
# ============================================================================

class TestRealOMVConnectorExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(OMVAuthenticationError, OMVConnectionError))
        self.assertTrue(issubclass(OMVReadonlyViolationError, OMVConnectionError))
        self.assertTrue(issubclass(OMVTimeoutError, OMVConnectionError))

    def test_config_preserves_all_fields(self):
        config = OMVConnectionConfig(
            host="omv.local", port=443,
            verify_ssl=False, timeout_seconds=60,
        )
        self.assertEqual(config.host, "omv.local")
        self.assertEqual(config.port, 443)
        self.assertFalse(config.verify_ssl)
        self.assertEqual(config.timeout_seconds, 60)

    def test_config_repr_no_secrets(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        r = repr(config)
        for term in ["password", "secret", "token", "api_key", "private_key"]:
            self.assertNotIn(term, r.lower())

    def test_config_no_password(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "password"))

    def test_config_no_secret(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "secret"))

    def test_config_no_token(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "token"))

    def test_config_no_api_key(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "api_key"))

    def test_config_no_private_key(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "private_key"))

    def test_config_no_credential(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "credential"))

    def test_config_whitespace_host_rejected(self):
        with self.assertRaises(OMVConnectionError):
            OMVConnectionConfig(
                host="   ", port=80,
                verify_ssl=True, timeout_seconds=30,
            )

    def test_config_large_port(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=65535,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.port, 65535)

    def test_config_large_timeout(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=3600,
        )
        self.assertEqual(config.timeout_seconds, 3600)

    def test_config_ssl_false(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=False, timeout_seconds=30,
        )
        self.assertFalse(config.verify_ssl)

    def test_state_all_values(self):
        for state in OMVRuntimeState:
            self.assertIsInstance(state.value, str)

    def test_connector_state_property(self):
        connector = RealOMVAPIConnector()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_connector_connect_then_state(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, OMVRuntimeState.CONNECTED)

    def test_connector_close_then_state(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_connector_execute_storage_status(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("storage_status")
        self.assertEqual(result["operation"], "storage_status")

    def test_connector_execute_service_status(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("service_status")
        self.assertEqual(result["operation"], "service_status")

    def test_connector_execute_delete_rejected(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(OMVReadonlyViolationError):
            connector.execute_readonly("delete_share")

    def test_connector_execute_write_rejected(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(OMVReadonlyViolationError):
            connector.execute_readonly("write_file")

    def test_connector_execute_upload_rejected(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        with self.assertRaises(OMVReadonlyViolationError):
            connector.execute_readonly("upload_file")

    def test_connector_not_connected_execute(self):
        connector = RealOMVAPIConnector()
        with self.assertRaises(OMVConnectionError):
            connector.execute_readonly("system_info")

    def test_connector_double_close(self):
        connector = RealOMVAPIConnector()
        connector.close()
        connector.close()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_connector_reconnect_execute(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        connector.close()
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["operation"], "system_info")

    def test_error_messages_safe(self):
        try:
            raise OMVConnectionError("test")
        except OMVConnectionError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "api_key", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_auth_error_message(self):
        exc = OMVAuthenticationError("auth failed")
        self.assertIn("auth failed", str(exc))

    def test_timeout_error_message(self):
        exc = OMVTimeoutError("timeout")
        self.assertIn("timeout", str(exc))

    def test_readonly_violation_message(self):
        exc = OMVReadonlyViolationError("forbidden")
        self.assertIn("forbidden", str(exc))

    def test_connector_result_has_status(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertIn("status", result)

    def test_connector_result_has_message(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertIn("message", result)

    def test_connector_result_contract_only(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertEqual(result["status"], "contract_only")

    def test_allowed_operations_frozenset(self):
        self.assertIsInstance(ALLOWED_READONLY_OPERATIONS, frozenset)

    def test_validate_operation_type_check(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation(123)

    def test_client_connect_close_lifecycle(self):
        class MockClient(OMVAPIClient):
            def __init__(self):
                self.connected = False
            def connect(self, config):
                self.connected = True
            def close(self):
                self.connected = False
        client = MockClient()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        client.connect(config)
        self.assertTrue(client.connected)
        client.close()
        self.assertFalse(client.connected)

    def test_executor_returns_dict(self):
        class MockExecutor(OMVReadOnlyExecutor):
            def execute(self, operation):
                return {"operation": operation, "status": "ok"}
        executor = MockExecutor()
        result = executor.execute("system_info")
        self.assertIsInstance(result, dict)

    def test_config_no_command(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "command"))

    def test_config_no_ssh(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertFalse(hasattr(config, "ssh"))

    def test_exception_hierarchy_omv_runtime(self):
        self.assertTrue(issubclass(OMVConnectionError, Exception))
        self.assertTrue(issubclass(OMVAuthenticationError, OMVConnectionError))
        self.assertTrue(issubclass(OMVReadonlyViolationError, OMVConnectionError))
        self.assertTrue(issubclass(OMVTimeoutError, OMVConnectionError))

    def test_connector_result_returns_dict(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        result = connector.execute_readonly("system_info")
        self.assertIsInstance(result, dict)

    def test_omv_api_connector_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVAPIConnector, ABC))

    def test_config_hostname(self):
        config = OMVConnectionConfig(
            host="omv.example.com", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.host, "omv.example.com")

    def test_config_ipv6(self):
        config = OMVConnectionConfig(
            host="::1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.host, "::1")

    def test_config_port_1(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=1,
            verify_ssl=True, timeout_seconds=30,
        )
        self.assertEqual(config.port, 1)

    def test_config_timeout_1(self):
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=1,
        )
        self.assertEqual(config.timeout_seconds, 1)

    def test_connector_status_transitions(self):
        connector = RealOMVAPIConnector()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        self.assertEqual(connector.state, OMVRuntimeState.CONNECTED)
        connector.close()
        self.assertEqual(connector.state, OMVRuntimeState.DISCONNECTED)

    def test_connector_multiple_configs(self):
        connector = RealOMVAPIConnector()
        for host in ["192.168.1.1", "10.0.0.1", "omv.local"]:
            config = OMVConnectionConfig(
                host=host, port=80,
                verify_ssl=True, timeout_seconds=30,
            )
            connector.connect(config)
            self.assertEqual(connector.state, OMVRuntimeState.CONNECTED)
            connector.close()

    def test_connector_execute_all_allowed(self):
        connector = RealOMVAPIConnector()
        config = OMVConnectionConfig(
            host="192.168.1.1", port=80,
            verify_ssl=True, timeout_seconds=30,
        )
        connector.connect(config)
        for op in ["system_info", "storage_status", "service_status"]:
            result = connector.execute_readonly(op)
            self.assertEqual(result["operation"], op)

    def test_validate_backtick_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("`id`")

    def test_validate_dollar_paren_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("$(id)")

    def test_validate_chmod_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("chmod 777 /tmp")

    def test_validate_dd_rejected(self):
        with self.assertRaises(OMVReadonlyViolationError):
            validate_omv_readonly_operation("dd if=/dev/zero of=/tmp/test")

    def test_state_disconnected_value(self):
        self.assertEqual(OMVRuntimeState.DISCONNECTED.value, "disconnected")

    def test_state_connecting_value(self):
        self.assertEqual(OMVRuntimeState.CONNECTING.value, "connecting")

    def test_state_connected_value(self):
        self.assertEqual(OMVRuntimeState.CONNECTED.value, "connected")

    def test_state_failed_value(self):
        self.assertEqual(OMVRuntimeState.FAILED.value, "failed")


if __name__ == "__main__":
    unittest.main()
