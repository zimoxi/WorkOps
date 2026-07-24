"""
WorkOps ReadOnly Runtime Tests
Sprint052: ReadOnly Runtime Connector Foundation

覆盖：
- RuntimeMode enum
- RuntimeRequest validation
- RuntimeResult validation
- ReadOnlyRuntimeConnector contract
- READ_ONLY enforcement
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.runtime.mode import RuntimeMode
from backup_manager.runtime.request import RuntimeRequest
from backup_manager.runtime.result import RuntimeResult
from backup_manager.runtime.connector import ReadOnlyRuntimeConnector
from backup_manager.runtime.errors import (
    RuntimeError,
    InvalidRuntimeRequestError,
    RuntimeExecutionError,
    RuntimeUnavailableError,
)


# ============================================================================
# RuntimeMode
# ============================================================================

class TestRuntimeMode(unittest.TestCase):
    """运行时模式测试"""

    def test_read_only(self):
        self.assertEqual(RuntimeMode.READ_ONLY.value, "read_only")

    def test_mutation(self):
        self.assertEqual(RuntimeMode.MUTATION.value, "mutation")

    def test_two_modes(self):
        self.assertEqual(len(RuntimeMode), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RuntimeMode("nonexistent")


# ============================================================================
# RuntimeRequest
# ============================================================================

class TestRuntimeRequest(unittest.TestCase):
    """运行时请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "execution_id": "exec-001",
            "adapter_id": "linux-001",
            "operation": "query_system",
            "mode": RuntimeMode.READ_ONLY,
        }
        defaults.update(kwargs)
        return RuntimeRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.operation, "query_system")
        self.assertEqual(req.mode, RuntimeMode.READ_ONLY)

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.execution_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            self._make_request(execution_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            self._make_request(adapter_id="")

    def test_empty_operation_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            self._make_request(operation="")

    def test_mutation_mode_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            self._make_request(mode=RuntimeMode.MUTATION)

    def test_invalid_mode_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            self._make_request(mode="read_only")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "shell"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RuntimeResult
# ============================================================================

class TestRuntimeResult(unittest.TestCase):
    """运行时结果测试"""

    def test_valid_result(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        self.assertEqual(result.execution_id, "exec-001")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    def test_frozen(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.execution_id = "other"

    def test_slots(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            RuntimeResult(execution_id="", success=True, message="ok")

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            RuntimeResult(execution_id="exec-001", success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            RuntimeResult(execution_id="exec-001", success=True, message=123)

    def test_timezone_aware(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_no_forbidden_fields(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_failed_result(self):
        result = RuntimeResult(
            execution_id="exec-001", success=False, message="error",
        )
        self.assertFalse(result.success)


# ============================================================================
# ReadOnlyRuntimeConnector Contract
# ============================================================================

class TestReadOnlyRuntimeConnectorContract(unittest.TestCase):
    """只读运行时连接器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(ReadOnlyRuntimeConnector, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(ReadOnlyRuntimeConnector, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ReadOnlyRuntimeConnector()

    def test_concrete_subclass(self):
        class MockConnector(ReadOnlyRuntimeConnector):
            def execute(self, request):
                return RuntimeResult(
                    execution_id=request.execution_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        result = connector.execute(req)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadConnector(ReadOnlyRuntimeConnector):
            pass
        with self.assertRaises(TypeError):
            BadConnector()


# ============================================================================
# Error Model
# ============================================================================

class TestRuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_runtime_error(self):
        with self.assertRaises(RuntimeError):
            raise RuntimeError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(RuntimeError):
            raise InvalidRuntimeRequestError("test")

    def test_execution_error(self):
        with self.assertRaises(RuntimeError):
            raise RuntimeExecutionError("test")

    def test_unavailable_error(self):
        with self.assertRaises(RuntimeError):
            raise RuntimeUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (RuntimeError, ("test",)),
            (InvalidRuntimeRequestError, ("test",)),
            (RuntimeExecutionError, ("test",)),
            (RuntimeUnavailableError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_request_no_credentials(self):
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "shell"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        runtime_dir = os.path.join("backup_manager", "runtime")
        for filename in os.listdir(runtime_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(runtime_dir, filename)
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
        runtime_dir = os.path.join("backup_manager", "runtime")
        for filename in os.listdir(runtime_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(runtime_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_connector_lifecycle(self):
        """完整连接器生命周期"""
        class MockConnector(ReadOnlyRuntimeConnector):
            def execute(self, request):
                return RuntimeResult(
                    execution_id=request.execution_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        result = connector.execute(req)
        self.assertTrue(result.success)
        self.assertEqual(result.execution_id, "exec-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestReadOnlyRuntimeExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidRuntimeRequestError, RuntimeError))
        self.assertTrue(issubclass(RuntimeExecutionError, RuntimeError))
        self.assertTrue(issubclass(RuntimeUnavailableError, RuntimeError))

    def test_request_repr_no_secrets(self):
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            RuntimeRequest(
                execution_id="   ", adapter_id="linux-001",
                operation="query_system", mode=RuntimeMode.READ_ONLY,
            )

    def test_request_whitespace_adapter_id_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            RuntimeRequest(
                execution_id="exec-001", adapter_id="   ",
                operation="query_system", mode=RuntimeMode.READ_ONLY,
            )

    def test_request_whitespace_operation_rejected(self):
        with self.assertRaises(InvalidRuntimeRequestError):
            RuntimeRequest(
                execution_id="exec-001", adapter_id="linux-001",
                operation="   ", mode=RuntimeMode.READ_ONLY,
            )

    def test_result_empty_message_accepted(self):
        result = RuntimeResult(execution_id="exec-001", success=True, message="")
        self.assertEqual(result.message, "")

    def test_connector_returns_result(self):
        class MockConnector(ReadOnlyRuntimeConnector):
            def execute(self, request):
                return RuntimeResult(
                    execution_id=request.execution_id,
                    success=True, message="ok",
                )
        connector = MockConnector()
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        result = connector.execute(req)
        self.assertIsInstance(result, RuntimeResult)

    def test_error_messages_safe(self):
        try:
            raise RuntimeError("test")
        except RuntimeError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_request_no_command(self):
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(req, "command"))

    def test_result_no_command(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "command"))

    def test_request_all_operations(self):
        for op in ["query_system", "query_storage", "query_network", "query_service"]:
            req = RuntimeRequest(
                execution_id="exec-001", adapter_id="linux-001",
                operation=op, mode=RuntimeMode.READ_ONLY,
            )
            self.assertEqual(req.operation, op)

    def test_connector_failed_result(self):
        class MockConnector(ReadOnlyRuntimeConnector):
            def execute(self, request):
                return RuntimeResult(
                    execution_id=request.execution_id,
                    success=False, message="error",
                )
        connector = MockConnector()
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        result = connector.execute(req)
        self.assertFalse(result.success)

    def test_request_preserves_all_fields(self):
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.operation, "query_system")
        self.assertEqual(req.mode, RuntimeMode.READ_ONLY)

    def test_result_preserves_all_fields(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        self.assertEqual(result.execution_id, "exec-001")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    def test_runtime_mode_read_only_only(self):
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        self.assertEqual(req.mode, RuntimeMode.READ_ONLY)

    def test_error_messages_safe_all(self):
        try:
            raise InvalidRuntimeRequestError("test")
        except InvalidRuntimeRequestError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_execution_error_message(self):
        exc = RuntimeExecutionError("exec failed")
        self.assertIn("exec failed", str(exc))

    def test_unavailable_error_message(self):
        exc = RuntimeUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_request_no_shell(self):
        req = RuntimeRequest(
            execution_id="exec-001", adapter_id="linux-001",
            operation="query_system", mode=RuntimeMode.READ_ONLY,
        )
        self.assertFalse(hasattr(req, "shell"))

    def test_result_no_stderr(self):
        result = RuntimeResult(
            execution_id="exec-001", success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))


if __name__ == "__main__":
    unittest.main()
