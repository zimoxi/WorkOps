"""
WorkOps OMV API Runtime Tests
Sprint060: OMV API Runtime Foundation

覆盖：
- OMVRuntimeMode enum
- OMVRuntimeSession validation
- OMVAPIRequest validation
- OMVRuntimeResult validation
- OMVAPIConnector contract
- validate_omv_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.runtime.omv.model import OMVRuntimeMode, OMVRuntimeSession
from backup_manager.runtime.omv.request import OMVAPIRequest, validate_omv_request
from backup_manager.runtime.omv.result import OMVRuntimeResult
from backup_manager.runtime.omv.connector import OMVAPIConnector
from backup_manager.runtime.omv.errors import (
    OMVRuntimeError,
    InvalidOMVRuntimeSessionError,
    OMVExecutionRejectedError,
    OMVConnectionUnavailableError,
)


# ============================================================================
# OMVRuntimeMode
# ============================================================================

class TestOMVRuntimeMode(unittest.TestCase):
    """OMV 运行时模式测试"""

    def test_read_only(self):
        self.assertEqual(OMVRuntimeMode.READ_ONLY.value, "read_only")

    def test_mutation(self):
        self.assertEqual(OMVRuntimeMode.MUTATION.value, "mutation")

    def test_two_modes(self):
        self.assertEqual(len(OMVRuntimeMode), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            OMVRuntimeMode("nonexistent")


# ============================================================================
# OMVRuntimeSession
# ============================================================================

class TestOMVRuntimeSession(unittest.TestCase):
    """OMV 运行时会话测试"""

    def _make_session(self, **kwargs):
        defaults = {
            "session_id": "omv-sess-001",
            "adapter_id": "omv-001",
            "mode": OMVRuntimeMode.READ_ONLY,
        }
        defaults.update(kwargs)
        return OMVRuntimeSession(**defaults)

    def test_valid_session(self):
        session = self._make_session()
        self.assertEqual(session.session_id, "omv-sess-001")
        self.assertEqual(session.adapter_id, "omv-001")
        self.assertEqual(session.mode, OMVRuntimeMode.READ_ONLY)

    def test_frozen(self):
        session = self._make_session()
        with self.assertRaises(AttributeError):
            session.session_id = "other"

    def test_slots(self):
        session = self._make_session()
        with self.assertRaises(AttributeError):
            session.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            self._make_session(session_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            self._make_session(adapter_id="")

    def test_invalid_mode_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            self._make_session(mode="read_only")

    def test_mutation_mode_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            self._make_session(mode=OMVRuntimeMode.MUTATION)

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
# OMVAPIRequest
# ============================================================================

class TestOMVAPIRequest(unittest.TestCase):
    """OMV API 请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "session_id": "omv-sess-001",
            "operation": "query_system",
        }
        defaults.update(kwargs)
        return OMVAPIRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.session_id, "omv-sess-001")
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
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            self._make_request(session_id="")

    def test_empty_operation_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
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
# OMVRuntimeResult
# ============================================================================

class TestOMVRuntimeResult(unittest.TestCase):
    """OMV 运行时结果测试"""

    def test_valid_result(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        self.assertEqual(result.session_id, "omv-sess-001")
        self.assertTrue(result.success)

    def test_frozen(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.session_id = "other"

    def test_slots(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_session_id_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            OMVRuntimeResult(session_id="", success=True, message="ok")

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            OMVRuntimeResult(session_id="omv-sess-001", success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            OMVRuntimeResult(session_id="omv-sess-001", success=True, message=123)

    def test_timezone_aware(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_failed_result(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=False, message="error",
        )
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# OMVAPIConnector Contract
# ============================================================================

class TestOMVAPIConnectorContract(unittest.TestCase):
    """OMV API 连接器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVAPIConnector, ABC))

    def test_has_connect(self):
        self.assertTrue(hasattr(OMVAPIConnector, "connect"))

    def test_has_execute_readonly(self):
        self.assertTrue(hasattr(OMVAPIConnector, "execute_readonly"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OMVAPIConnector()

    def test_concrete_subclass(self):
        class MockConnector(OMVAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return OMVRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        connector.connect(session)
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)

    def test_missing_connect(self):
        class BadConnector(OMVAPIConnector):
            def execute_readonly(self, request):
                pass
        with self.assertRaises(TypeError):
            BadConnector()

    def test_missing_execute_readonly(self):
        class BadConnector(OMVAPIConnector):
            def connect(self, session):
                pass
        with self.assertRaises(TypeError):
            BadConnector()


# ============================================================================
# validate_omv_request
# ============================================================================

class TestValidateOMVRequest(unittest.TestCase):
    """验证 OMV 请求测试"""

    def test_valid_request(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        validate_omv_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            validate_omv_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestOMVRuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_runtime_error(self):
        with self.assertRaises(OMVRuntimeError):
            raise OMVRuntimeError("test")

    def test_invalid_session_error(self):
        with self.assertRaises(OMVRuntimeError):
            raise InvalidOMVRuntimeSessionError("test")

    def test_execution_rejected_error(self):
        with self.assertRaises(OMVRuntimeError):
            raise OMVExecutionRejectedError("test")

    def test_connection_unavailable_error(self):
        with self.assertRaises(OMVRuntimeError):
            raise OMVConnectionUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (OMVRuntimeError, ("test",)),
            (InvalidOMVRuntimeSessionError, ("test",)),
            (OMVExecutionRejectedError, ("test",)),
            (OMVConnectionUnavailableError, ("test",)),
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
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        for attr in ["password", "credential", "secret", "token", "api_key", "ssh", "private_key"]:
            self.assertFalse(hasattr(session, attr))

    def test_request_no_credentials(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        for attr in ["mutation", "delete", "create", "update", "command", "secret", "token"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

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
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

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
        class MockConnector(OMVAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return OMVRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        connector.connect(session)
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)
        self.assertEqual(result.session_id, "omv-sess-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestOMVAPIRuntimeExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidOMVRuntimeSessionError, OMVRuntimeError))
        self.assertTrue(issubclass(OMVExecutionRejectedError, OMVRuntimeError))
        self.assertTrue(issubclass(OMVConnectionUnavailableError, OMVRuntimeError))

    def test_session_repr_no_secrets(self):
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        r = repr(session)
        for term in ["password", "secret", "token", "api_key"]:
            self.assertNotIn(term, r.lower())

    def test_request_repr_no_secrets(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        r = repr(req)
        for term in ["password", "secret", "token", "command"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_session_preserves_all_fields(self):
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        self.assertEqual(session.session_id, "omv-sess-001")
        self.assertEqual(session.adapter_id, "omv-001")
        self.assertEqual(session.mode, OMVRuntimeMode.READ_ONLY)

    def test_request_preserves_all_fields(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        self.assertEqual(req.session_id, "omv-sess-001")
        self.assertEqual(req.operation, "query_system")

    def test_connector_returns_result(self):
        class MockConnector(OMVAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return OMVRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertIsInstance(result, OMVRuntimeResult)

    def test_connector_failed_result(self):
        class MockConnector(OMVAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return OMVRuntimeResult(
                    session_id=request.session_id,
                    success=False, message="error",
                )
        connector = MockConnector()
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertFalse(result.success)

    def test_session_whitespace_id_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            OMVRuntimeSession(
                session_id="   ", adapter_id="omv-001",
                mode=OMVRuntimeMode.READ_ONLY,
            )

    def test_request_whitespace_session_id_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            OMVAPIRequest(session_id="   ", operation="query_system")

    def test_request_whitespace_operation_rejected(self):
        with self.assertRaises(InvalidOMVRuntimeSessionError):
            OMVAPIRequest(session_id="omv-sess-001", operation="   ")

    def test_result_empty_message_accepted(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="",
        )
        self.assertEqual(result.message, "")

    def test_session_no_api_key(self):
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "api_key"))

    def test_request_no_command(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "command"))

    def test_result_no_stderr(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))

    def test_connector_connect_then_execute(self):
        class MockConnector(OMVAPIConnector):
            def __init__(self):
                self.connected = False
            def connect(self, session):
                self.connected = True
            def execute_readonly(self, request):
                return OMVRuntimeResult(
                    session_id=request.session_id,
                    success=self.connected, message="ok" if self.connected else "not connected",
                )
        connector = MockConnector()
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        connector.connect(session)
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertTrue(result.success)

    def test_error_messages_safe(self):
        try:
            raise OMVRuntimeError("test")
        except OMVRuntimeError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_connector_execute_returns_result(self):
        class MockConnector(OMVAPIConnector):
            def connect(self, session):
                pass
            def execute_readonly(self, request):
                return OMVRuntimeResult(
                    session_id=request.session_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        result = connector.execute_readonly(req)
        self.assertIsInstance(result, OMVRuntimeResult)

    def test_request_all_operations(self):
        for op in ["query_system", "query_storage", "query_share", "query_backup"]:
            req = OMVAPIRequest(session_id="omv-sess-001", operation=op)
            self.assertEqual(req.operation, op)

    def test_result_all_success_states(self):
        for success in [True, False]:
            result = OMVRuntimeResult(
                session_id="omv-sess-001", success=success, message="ok",
            )
            self.assertEqual(result.success, success)

    def test_session_no_private_key(self):
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "private_key"))

    def test_session_no_ssh(self):
        session = OMVRuntimeSession(
            session_id="omv-sess-001", adapter_id="omv-001",
            mode=OMVRuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(session, "ssh"))

    def test_request_no_delete(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "delete"))

    def test_request_no_create(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "create"))

    def test_request_no_update(self):
        req = OMVAPIRequest(session_id="omv-sess-001", operation="query_system")
        self.assertFalse(hasattr(req, "update"))

    def test_result_no_stdout(self):
        result = OMVRuntimeResult(
            session_id="omv-sess-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stdout"))

    def test_conflict_error_message(self):
        exc = OMVConnectionUnavailableError("connection refused")
        self.assertIn("connection refused", str(exc))

    def test_rejected_error_message(self):
        exc = OMVExecutionRejectedError("mutation not allowed")
        self.assertIn("mutation not allowed", str(exc))

    def test_invalid_session_error_message(self):
        exc = InvalidOMVRuntimeSessionError("invalid session")
        self.assertIn("invalid session", str(exc))


if __name__ == "__main__":
    unittest.main()
