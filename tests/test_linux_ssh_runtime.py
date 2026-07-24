"""
WorkOps Linux SSH Runtime Tests
Sprint058: Linux SSH Runtime Foundation

覆盖：
- SSHSessionMode enum
- SSHSession validation
- SSHExecutionRequest validation
- SSHRuntimeResult validation
- LinuxSSHConnector contract
- validate_ssh_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.runtime.ssh.model import SSHSessionMode, SSHSession
from backup_manager.runtime.ssh.session import SSHExecutionRequest, validate_ssh_request
from backup_manager.runtime.ssh.result import SSHRuntimeResult
from backup_manager.runtime.ssh.connector import LinuxSSHConnector
from backup_manager.runtime.ssh.errors import (
    SSHRuntimeError,
    InvalidSSHSessionError,
    SSHExecutionRejectedError,
    SSHConnectionUnavailableError,
)


# ============================================================================
# SSHSessionMode
# ============================================================================

class TestSSHSessionMode(unittest.TestCase):
    """SSH 会话模式测试"""

    def test_read_only(self):
        self.assertEqual(SSHSessionMode.READ_ONLY.value, "read_only")

    def test_mutation(self):
        self.assertEqual(SSHSessionMode.MUTATION.value, "mutation")

    def test_two_modes(self):
        self.assertEqual(len(SSHSessionMode), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            SSHSessionMode("nonexistent")


# ============================================================================
# SSHSession
# ============================================================================

class TestSSHSession(unittest.TestCase):
    """SSH 会话测试"""

    def _make_session(self, **kwargs):
        defaults = {
            "session_id": "sess-001",
            "adapter_id": "linux-001",
            "mode": SSHSessionMode.READ_ONLY,
        }
        defaults.update(kwargs)
        return SSHSession(**defaults)

    def test_valid_session(self):
        session = self._make_session()
        self.assertEqual(session.session_id, "sess-001")
        self.assertEqual(session.adapter_id, "linux-001")
        self.assertEqual(session.mode, SSHSessionMode.READ_ONLY)

    def test_frozen(self):
        session = self._make_session()
        with self.assertRaises(AttributeError):
            session.session_id = "other"

    def test_slots(self):
        session = self._make_session()
        with self.assertRaises(AttributeError):
            session.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            self._make_session(session_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            self._make_session(adapter_id="")

    def test_invalid_mode_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            self._make_session(mode="read_only")

    def test_mutation_mode_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            self._make_session(mode=SSHSessionMode.MUTATION)

    def test_timezone_aware(self):
        session = self._make_session()
        self.assertIsNotNone(session.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        session = self._make_session()
        for attr in ["password", "credential", "secret", "token", "private_key", "ssh_key"]:
            self.assertFalse(hasattr(session, attr))

    def test_repr_no_secrets(self):
        session = self._make_session()
        r = repr(session)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# SSHExecutionRequest
# ============================================================================

class TestSSHExecutionRequest(unittest.TestCase):
    """SSH 执行请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "session_id": "sess-001",
            "operation": "query_system",
        }
        defaults.update(kwargs)
        return SSHExecutionRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.session_id, "sess-001")
        self.assertEqual(req.operation, "query_system")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.session_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            self._make_request(session_id="")

    def test_empty_operation_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            self._make_request(operation="")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["shell", "command", "script", "sudo", "password", "token"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "command"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# SSHRuntimeResult
# ============================================================================

class TestSSHRuntimeResult(unittest.TestCase):
    """SSH 运行时结果测试"""

    def test_valid_result(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        self.assertEqual(result.session_id, "sess-001")
        self.assertTrue(result.success)

    def test_frozen(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.session_id = "other"

    def test_slots(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            SSHRuntimeResult(session_id="", success=True, message="ok")

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidSSHSessionError):
            SSHRuntimeResult(session_id="sess-001", success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidSSHSessionError):
            SSHRuntimeResult(session_id="sess-001", success=True, message=123)

    def test_timezone_aware(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_failed_result(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=False, message="error",
        )
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "shell", "secret", "credential"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# LinuxSSHConnector Contract
# ============================================================================

class TestLinuxSSHConnectorContract(unittest.TestCase):
    """Linux SSH 连接器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(LinuxSSHConnector, ABC))

    def test_has_connect(self):
        self.assertTrue(hasattr(LinuxSSHConnector, "connect"))

    def test_has_execute_readonly(self):
        self.assertTrue(hasattr(LinuxSSHConnector, "execute_readonly"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            LinuxSSHConnector()

    def test_concrete_subclass(self):
        class MockConnector(LinuxSSHConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return SSHRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        connector.connect(session)
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)

    def test_missing_connect(self):
        class BadConnector(LinuxSSHConnector):
            def execute_readonly(self, request):
                pass
        with self.assertRaises(TypeError):
            BadConnector()

    def test_missing_execute_readonly(self):
        class BadConnector(LinuxSSHConnector):
            def connect(self, session):
                pass
        with self.assertRaises(TypeError):
            BadConnector()


# ============================================================================
# validate_ssh_request
# ============================================================================

class TestValidateSSHRequest(unittest.TestCase):
    """验证 SSH 请求测试"""

    def test_valid_request(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        validate_ssh_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            validate_ssh_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestSSHRuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_runtime_error(self):
        with self.assertRaises(SSHRuntimeError):
            raise SSHRuntimeError("test")

    def test_invalid_session_error(self):
        with self.assertRaises(SSHRuntimeError):
            raise InvalidSSHSessionError("test")

    def test_execution_rejected_error(self):
        with self.assertRaises(SSHRuntimeError):
            raise SSHExecutionRejectedError("test")

    def test_connection_unavailable_error(self):
        with self.assertRaises(SSHRuntimeError):
            raise SSHConnectionUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (SSHRuntimeError, ("test",)),
            (InvalidSSHSessionError, ("test",)),
            (SSHExecutionRejectedError, ("test",)),
            (SSHConnectionUnavailableError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_session_no_credentials(self):
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        for attr in ["password", "credential", "secret", "token", "private_key", "ssh_key"]:
            self.assertFalse(hasattr(session, attr))

    def test_request_no_credentials(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        for attr in ["shell", "command", "script", "sudo", "password", "token"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "shell", "secret", "credential"]:
            self.assertFalse(hasattr(result, attr))

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
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

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
        class MockConnector(LinuxSSHConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return SSHRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        connector.connect(session)
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)
        self.assertEqual(result.session_id, "sess-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestLinuxSSHRuntimeExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidSSHSessionError, SSHRuntimeError))
        self.assertTrue(issubclass(SSHExecutionRejectedError, SSHRuntimeError))
        self.assertTrue(issubclass(SSHConnectionUnavailableError, SSHRuntimeError))

    def test_session_repr_no_secrets(self):
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        r = repr(session)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_repr_no_secrets(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        r = repr(req)
        for term in ["password", "secret", "token", "command"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_session_preserves_all_fields(self):
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        self.assertEqual(session.session_id, "sess-001")
        self.assertEqual(session.adapter_id, "linux-001")
        self.assertEqual(session.mode, SSHSessionMode.READ_ONLY)

    def test_request_preserves_all_fields(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        self.assertEqual(req.session_id, "sess-001")
        self.assertEqual(req.operation, "query_system")

    def test_connector_returns_result(self):
        class MockConnector(LinuxSSHConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return SSHRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertIsInstance(result, SSHRuntimeResult)

    def test_connector_failed_result(self):
        class MockConnector(LinuxSSHConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return SSHRuntimeResult(
                    session_id=request.session_id,
                    success=False, message="error",
                )
        connector = MockConnector()
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertFalse(result.success)

    def test_session_whitespace_id_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            SSHSession(
                session_id="   ", adapter_id="linux-001",
                mode=SSHSessionMode.READ_ONLY,
            )

    def test_request_whitespace_session_id_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            SSHExecutionRequest(session_id="   ", operation="query_system")

    def test_request_whitespace_operation_rejected(self):
        with self.assertRaises(InvalidSSHSessionError):
            SSHExecutionRequest(session_id="sess-001", operation="   ")

    def test_result_empty_message_accepted(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="",
        )
        self.assertEqual(result.message, "")

    def test_session_no_command(self):
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "command"))

    def test_request_no_shell(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "shell"))

    def test_result_no_stderr(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))

    def test_error_messages_safe(self):
        try:
            raise SSHRuntimeError("test")
        except SSHRuntimeError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_session_all_modes_read_only(self):
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        self.assertEqual(session.mode, SSHSessionMode.READ_ONLY)

    def test_request_all_operations(self):
        for op in ["query_system", "query_storage", "query_network", "query_service"]:
            req = SSHExecutionRequest(session_id="sess-001", operation=op)
            self.assertEqual(req.operation, op)

    def test_result_all_success_states(self):
        for success in [True, False]:
            result = SSHRuntimeResult(
                session_id="sess-001", success=success, message="ok",
            )
            self.assertEqual(result.success, success)

    def test_connector_connect_then_execute(self):
        class MockConnector(LinuxSSHConnector):
            def __init__(self):
                self.connected = False
            def connect(self, session):
                self.connected = True
            def execute_readonly(self, request):
                return SSHRuntimeResult(
                    session_id=request.session_id,
                    success=self.connected, message="ok" if self.connected else "not connected",
                )
        connector = MockConnector()
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        connector.connect(session)
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)

    def test_session_no_ssh_key(self):
        session = SSHSession(
            session_id="sess-001", adapter_id="linux-001",
            mode=SSHSessionMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "ssh_key"))

    def test_request_no_sudo(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "sudo"))

    def test_request_no_script(self):
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "script"))

    def test_result_no_command(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "command"))

    def test_result_no_shell(self):
        result = SSHRuntimeResult(
            session_id="sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "shell"))

    def test_conflict_error_message(self):
        exc = SSHConnectionUnavailableError("connection refused")
        self.assertIn("connection refused", str(exc))

    def test_rejected_error_message(self):
        exc = SSHExecutionRejectedError("mutation not allowed")
        self.assertIn("mutation not allowed", str(exc))

    def test_invalid_session_error_message(self):
        exc = InvalidSSHSessionError("invalid session")
        self.assertIn("invalid session", str(exc))

    def test_connector_execute_returns_result(self):
        class MockConnector(LinuxSSHConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return SSHRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = SSHExecutionRequest(session_id="sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertIsInstance(result, SSHRuntimeResult)


if __name__ == "__main__":
    unittest.main()
