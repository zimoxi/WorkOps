"""
WorkOps PVE API Runtime Tests
Sprint059: PVE API Runtime Foundation

覆盖：
- PVERuntimeMode enum
- PVERuntimeSession validation
- PVEAPIRequest validation
- PVERuntimeResult validation
- PVEAPIConnector contract
- validate_pve_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.runtime.pve.model import PVERuntimeMode, PVERuntimeSession
from backup_manager.runtime.pve.request import PVEAPIRequest, validate_pve_request
from backup_manager.runtime.pve.result import PVERuntimeResult
from backup_manager.runtime.pve.connector import PVEAPIConnector
from backup_manager.runtime.pve.errors import (
    PVERuntimeError,
    InvalidPVERuntimeSessionError,
    PVEExecutionRejectedError,
    PVEConnectionUnavailableError,
)


# ============================================================================
# PVERuntimeMode
# ============================================================================

class TestPVERuntimeMode(unittest.TestCase):
    """PVE 运行时模式测试"""

    def test_read_only(self):
        self.assertEqual(PVERuntimeMode.READ_ONLY.value, "read_only")

    def test_mutation(self):
        self.assertEqual(PVERuntimeMode.MUTATION.value, "mutation")

    def test_two_modes(self):
        self.assertEqual(len(PVERuntimeMode), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PVERuntimeMode("nonexistent")


# ============================================================================
# PVERuntimeSession
# ============================================================================

class TestPVERuntimeSession(unittest.TestCase):
    """PVE 运行时会话测试"""

    def _make_session(self, **kwargs):
        defaults = {
            "session_id": "pve-sess-001",
            "adapter_id": "pve-001",
            "mode": PVERuntimeMode.READ_ONLY,
        }
        defaults.update(kwargs)
        return PVERuntimeSession(**defaults)

    def test_valid_session(self):
        session = self._make_session()
        self.assertEqual(session.session_id, "pve-sess-001")
        self.assertEqual(session.adapter_id, "pve-001")
        self.assertEqual(session.mode, PVERuntimeMode.READ_ONLY)

    def test_frozen(self):
        session = self._make_session()
        with self.assertRaises(AttributeError):
            session.session_id = "other"

    def test_slots(self):
        session = self._make_session()
        with self.assertRaises(AttributeError):
            session.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            self._make_session(session_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            self._make_session(adapter_id="")

    def test_invalid_mode_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            self._make_session(mode="read_only")

    def test_mutation_mode_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            self._make_session(mode=PVERuntimeMode.MUTATION)

    def test_timezone_aware(self):
        session = self._make_session()
        self.assertIsNotNone(session.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        session = self._make_session()
        for attr in ["password", "credential", "secret", "token", "api_key", "ssh", "private_key"]:
            self.assertFalse(hasattr(session, attr))

    def test_repr_no_secrets(self):
        session = self._make_session()
        r = repr(session)
        for term in ["password", "secret", "token", "api_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# PVEAPIRequest
# ============================================================================

class TestPVEAPIRequest(unittest.TestCase):
    """PVE API 请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "session_id": "pve-sess-001",
            "operation": "query_node",
        }
        defaults.update(kwargs)
        return PVEAPIRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.session_id, "pve-sess-001")
        self.assertEqual(req.operation, "query_node")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.session_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            self._make_request(session_id="")

    def test_empty_operation_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            self._make_request(operation="")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["mutation", "delete", "create", "update", "command", "secret", "token"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "command"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# PVERuntimeResult
# ============================================================================

class TestPVERuntimeResult(unittest.TestCase):
    """PVE 运行时结果测试"""

    def test_valid_result(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        self.assertEqual(result.session_id, "pve-sess-001")
        self.assertTrue(result.success)

    def test_frozen(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.session_id = "other"

    def test_slots(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            PVERuntimeResult(session_id="", success=True, message="ok")

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            PVERuntimeResult(session_id="pve-sess-001", success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            PVERuntimeResult(session_id="pve-sess-001", success=True, message=123)

    def test_timezone_aware(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_failed_result(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=False, message="error",
        )
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# PVEAPIConnector Contract
# ============================================================================

class TestPVEAPIConnectorContract(unittest.TestCase):
    """PVE API 连接器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEAPIConnector, ABC))

    def test_has_connect(self):
        self.assertTrue(hasattr(PVEAPIConnector, "connect"))

    def test_has_execute_readonly(self):
        self.assertTrue(hasattr(PVEAPIConnector, "execute_readonly"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PVEAPIConnector()

    def test_concrete_subclass(self):
        class MockConnector(PVEAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return PVERuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        connector.connect(session)
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)

    def test_missing_connect(self):
        class BadConnector(PVEAPIConnector):
            def execute_readonly(self, request):
                pass
        with self.assertRaises(TypeError):
            BadConnector()

    def test_missing_execute_readonly(self):
        class BadConnector(PVEAPIConnector):
            def connect(self, session):
                pass
        with self.assertRaises(TypeError):
            BadConnector()


# ============================================================================
# validate_pve_request
# ============================================================================

class TestValidatePVERequest(unittest.TestCase):
    """验证 PVE 请求测试"""

    def test_valid_request(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        validate_pve_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            validate_pve_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestPVERuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_runtime_error(self):
        with self.assertRaises(PVERuntimeError):
            raise PVERuntimeError("test")

    def test_invalid_session_error(self):
        with self.assertRaises(PVERuntimeError):
            raise InvalidPVERuntimeSessionError("test")

    def test_execution_rejected_error(self):
        with self.assertRaises(PVERuntimeError):
            raise PVEExecutionRejectedError("test")

    def test_connection_unavailable_error(self):
        with self.assertRaises(PVERuntimeError):
            raise PVEConnectionUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (PVERuntimeError, ("test",)),
            (InvalidPVERuntimeSessionError, ("test",)),
            (PVEExecutionRejectedError, ("test",)),
            (PVEConnectionUnavailableError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "api_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_session_no_credentials(self):
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        for attr in ["password", "credential", "secret", "token", "api_key", "ssh", "private_key"]:
            self.assertFalse(hasattr(session, attr))

    def test_request_no_credentials(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        for attr in ["mutation", "delete", "create", "update", "command", "secret", "token"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

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
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

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
        class MockConnector(PVEAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return PVERuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        connector.connect(session)
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)
        self.assertEqual(result.session_id, "pve-sess-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestPVEAPIRuntimeExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidPVERuntimeSessionError, PVERuntimeError))
        self.assertTrue(issubclass(PVEExecutionRejectedError, PVERuntimeError))
        self.assertTrue(issubclass(PVEConnectionUnavailableError, PVERuntimeError))

    def test_session_repr_no_secrets(self):
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        r = repr(session)
        for term in ["password", "secret", "token", "api_key"]:
            self.assertNotIn(term, r.lower())

    def test_request_repr_no_secrets(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        r = repr(req)
        for term in ["password", "secret", "token", "command"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_session_preserves_all_fields(self):
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        self.assertEqual(session.session_id, "pve-sess-001")
        self.assertEqual(session.adapter_id, "pve-001")
        self.assertEqual(session.mode, PVERuntimeMode.READ_ONLY)

    def test_request_preserves_all_fields(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        self.assertEqual(req.session_id, "pve-sess-001")
        self.assertEqual(req.operation, "query_node")

    def test_connector_returns_result(self):
        class MockConnector(PVEAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return PVERuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        result = connector.execute_readonly(req)
        self.assertIsInstance(result, PVERuntimeResult)

    def test_connector_failed_result(self):
        class MockConnector(PVEAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return PVERuntimeResult(
                    session_id=request.session_id,
                    success=False, message="error",
                )
        connector = MockConnector()
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        result = connector.execute_readonly(req)
        self.assertFalse(result.success)

    def test_session_whitespace_id_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            PVERuntimeSession(
                session_id="   ", adapter_id="pve-001",
                mode=PVERuntimeMode.READ_ONLY,
            )

    def test_request_whitespace_session_id_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            PVEAPIRequest(session_id="   ", operation="query_node")

    def test_request_whitespace_operation_rejected(self):
        with self.assertRaises(InvalidPVERuntimeSessionError):
            PVEAPIRequest(session_id="pve-sess-001", operation="   ")

    def test_result_empty_message_accepted(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="",
        )
        self.assertEqual(result.message, "")

    def test_session_no_api_key(self):
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "api_key"))

    def test_request_no_command(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        self.assertFalse(hasattr(req, "command"))

    def test_result_no_stderr(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))

    def test_connector_connect_then_execute(self):
        class MockConnector(PVEAPIConnector):
            def __init__(self):
                self.connected = False
            def connect(self, session):
                self.connected = True
            def execute_readonly(self, request):
                return PVERuntimeResult(
                    session_id=request.session_id,
                    success=self.connected, message="ok" if self.connected else "not connected",
                )
        connector = MockConnector()
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        connector.connect(session)
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)

    def test_error_messages_safe(self):
        try:
            raise PVERuntimeError("test")
        except PVERuntimeError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_request_all_operations(self):
        for op in ["query_node", "query_vm", "query_storage", "query_backup"]:
            req = PVEAPIRequest(session_id="pve-sess-001", operation=op)
            self.assertEqual(req.operation, op)

    def test_result_all_success_states(self):
        for success in [True, False]:
            result = PVERuntimeResult(
                session_id="pve-sess-001", success=success, message="ok",
            )
            self.assertEqual(result.success, success)

    def test_session_no_private_key(self):
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "private_key"))

    def test_session_no_ssh(self):
        session = PVERuntimeSession(
            session_id="pve-sess-001", adapter_id="pve-001",
            mode=PVERuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "ssh"))

    def test_request_no_delete(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        self.assertFalse(hasattr(req, "delete"))

    def test_request_no_create(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        self.assertFalse(hasattr(req, "create"))

    def test_request_no_update(self):
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        self.assertFalse(hasattr(req, "update"))

    def test_result_no_stdout(self):
        result = PVERuntimeResult(
            session_id="pve-sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stdout"))

    def test_conflict_error_message(self):
        exc = PVEConnectionUnavailableError("connection refused")
        self.assertIn("connection refused", str(exc))

    def test_rejected_error_message(self):
        exc = PVEExecutionRejectedError("mutation not allowed")
        self.assertIn("mutation not allowed", str(exc))

    def test_invalid_session_error_message(self):
        exc = InvalidPVERuntimeSessionError("invalid session")
        self.assertIn("invalid session", str(exc))

    def test_connector_execute_returns_result(self):
        class MockConnector(PVEAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return PVERuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = PVEAPIRequest(session_id="pve-sess-001", operation="query_node")
        result = connector.execute_readonly(req)
        self.assertIsInstance(result, PVERuntimeResult)


if __name__ == "__main__":
    unittest.main()
