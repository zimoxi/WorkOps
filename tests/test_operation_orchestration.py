"""
WorkOps Operation Orchestration Tests
Sprint038: Operation Orchestration Foundation

覆盖：
- OperationType enum
- OperationStatus enum
- OperationRequest validation
- OperationResult validation
- OperationExecutor contract
- OperationRegistry
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.operations.operation import OperationType, OperationStatus
from backup_manager.operations.model import OperationRequest
from backup_manager.operations.result import OperationResult
from backup_manager.operations.executor import OperationExecutor
from backup_manager.operations.registry import OperationRegistry
from backup_manager.operations.errors import (
    OperationError,
    InvalidOperationError,
    OperationConflictError,
    OperationNotFoundError,
)


# ============================================================================
# OperationType
# ============================================================================

class TestOperationType(unittest.TestCase):
    """操作类型测试"""

    def test_backup(self):
        self.assertEqual(OperationType.BACKUP.value, "backup")

    def test_restore(self):
        self.assertEqual(OperationType.RESTORE.value, "restore")

    def test_health_check(self):
        self.assertEqual(OperationType.HEALTH_CHECK.value, "health_check")

    def test_inventory_scan(self):
        self.assertEqual(OperationType.INVENTORY_SCAN.value, "inventory_scan")

    def test_four_types(self):
        self.assertEqual(len(OperationType), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            OperationType("nonexistent")


# ============================================================================
# OperationStatus
# ============================================================================

class TestOperationStatus(unittest.TestCase):
    """操作状态测试"""

    def test_created(self):
        self.assertEqual(OperationStatus.CREATED.value, "created")

    def test_running(self):
        self.assertEqual(OperationStatus.RUNNING.value, "running")

    def test_success(self):
        self.assertEqual(OperationStatus.SUCCESS.value, "success")

    def test_failed(self):
        self.assertEqual(OperationStatus.FAILED.value, "failed")

    def test_cancelled(self):
        self.assertEqual(OperationStatus.CANCELLED.value, "cancelled")

    def test_five_statuses(self):
        self.assertEqual(len(OperationStatus), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            OperationStatus("nonexistent")


# ============================================================================
# OperationRequest
# ============================================================================

class TestOperationRequest(unittest.TestCase):
    """操作请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "operation_id": "op-001",
            "operation_type": OperationType.BACKUP,
            "device_id": "dev-001",
        }
        defaults.update(kwargs)
        return OperationRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.operation_id, "op-001")
        self.assertEqual(req.operation_type, OperationType.BACKUP)
        self.assertEqual(req.device_id, "dev-001")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.operation_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidOperationError):
            self._make_request(operation_id="")

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidOperationError):
            self._make_request(device_id="")

    def test_invalid_operation_type_rejected(self):
        with self.assertRaises(InvalidOperationError):
            self._make_request(operation_type="backup")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "ip", "hostname", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# OperationResult
# ============================================================================

class TestOperationResult(unittest.TestCase):
    """操作结果测试"""

    def test_valid_result(self):
        result = OperationResult(
            operation_id="op-001",
            status=OperationStatus.SUCCESS,
            success=True,
            message="done",
        )
        self.assertEqual(result.operation_id, "op-001")
        self.assertTrue(result.success)

    def test_frozen(self):
        result = OperationResult(
            operation_id="op-001", status=OperationStatus.SUCCESS,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.operation_id = "other"

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidOperationError):
            OperationResult(
                operation_id="", status=OperationStatus.SUCCESS,
                success=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidOperationError):
            OperationResult(
                operation_id="op-001", status="success",
                success=True, message="ok",
            )

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidOperationError):
            OperationResult(
                operation_id="op-001", status=OperationStatus.SUCCESS,
                success=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidOperationError):
            OperationResult(
                operation_id="op-001", status=OperationStatus.SUCCESS,
                success=True, message=123,
            )

    def test_timezone_aware(self):
        result = OperationResult(
            operation_id="op-001", status=OperationStatus.SUCCESS,
            success=True, message="ok",
        )
        self.assertIsNotNone(result.finished_at.tzinfo)

    def test_no_forbidden_fields(self):
        result = OperationResult(
            operation_id="op-001", status=OperationStatus.SUCCESS,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "shell", "command", "credential", "secret"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# OperationExecutor Contract
# ============================================================================

class TestOperationExecutorContract(unittest.TestCase):
    """执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OperationExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(OperationExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OperationExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(OperationExecutor):
            def execute(self, request):
                return OperationResult(
                    operation_id=request.operation_id,
                    status=OperationStatus.SUCCESS,
                    success=True,
                    message="ok",
                )
        executor = MockExecutor()
        req = OperationRequest(
            operation_id="op-001", operation_type=OperationType.BACKUP,
            device_id="dev-001",
        )
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadExecutor(OperationExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# OperationRegistry
# ============================================================================

class TestOperationRegistry(unittest.TestCase):
    """操作注册表测试"""

    def setUp(self):
        self.registry = OperationRegistry()

    def _make_executor(self):
        class MockExecutor(OperationExecutor):
            def execute(self, request):
                return OperationResult(
                    operation_id=request.operation_id,
                    status=OperationStatus.SUCCESS,
                    success=True, message="ok",
                )
        return MockExecutor()

    def test_register_and_get(self):
        executor = self._make_executor()
        self.registry.register("backup", executor)
        got = self.registry.get("backup")
        self.assertIs(got, executor)

    def test_duplicate_rejected(self):
        executor = self._make_executor()
        self.registry.register("backup", executor)
        with self.assertRaises(OperationConflictError):
            self.registry.register("backup", executor)

    def test_get_not_found(self):
        with self.assertRaises(OperationNotFoundError):
            self.registry.get("nonexistent")

    def test_list(self):
        self.registry.register("backup", self._make_executor())
        self.registry.register("restore", self._make_executor())
        types = self.registry.list()
        self.assertEqual(len(types), 2)

    def test_supports_true(self):
        self.registry.register("backup", self._make_executor())
        self.assertTrue(self.registry.supports("backup"))

    def test_supports_false(self):
        self.assertFalse(self.registry.supports("nonexistent"))

    def test_empty_type_rejected(self):
        with self.assertRaises(TypeError):
            self.registry.register("", self._make_executor())

    def test_non_executor_rejected(self):
        with self.assertRaises(TypeError):
            self.registry.register("bad", "not_an_executor")

    def test_no_dynamic_loading(self):
        import ast
        with open("backup_manager/operations/registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("__import__", "import_module"):
                    self.fail("registry uses dynamic import")

    def test_list_empty(self):
        self.assertEqual(self.registry.list(), [])


# ============================================================================
# Error Model
# ============================================================================

class TestOperationErrors(unittest.TestCase):
    """错误模型测试"""

    def test_operation_error(self):
        with self.assertRaises(OperationError):
            raise OperationError("test")

    def test_invalid_operation_error(self):
        with self.assertRaises(OperationError):
            raise InvalidOperationError("test")

    def test_conflict_error(self):
        exc = OperationConflictError("op-001")
        self.assertIn("op-001", str(exc))

    def test_not_found_error(self):
        exc = OperationNotFoundError("op-001")
        self.assertIn("op-001", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (OperationError, ("test",)),
            (InvalidOperationError, ("test",)),
            (OperationConflictError, ("op-001",)),
            (OperationNotFoundError, ("op-001",)),
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
        req = OperationRequest(
            operation_id="op-001", operation_type=OperationType.BACKUP,
            device_id="dev-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = OperationResult(
            operation_id="op-001", status=OperationStatus.SUCCESS,
            success=True, message="ok",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_registry_no_credentials(self):
        registry = OperationRegistry()
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(registry, attr))

    def test_no_subprocess(self):
        import ast
        import os
        ops_dir = os.path.join("backup_manager", "operations")
        for filename in os.listdir(ops_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(ops_dir, filename)
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
        ops_dir = os.path.join("backup_manager", "operations")
        for filename in os.listdir(ops_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(ops_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_registry_lifecycle(self):
        """完整注册表生命周期"""
        class MockExecutor(OperationExecutor):
            def execute(self, request):
                return OperationResult(
                    operation_id=request.operation_id,
                    status=OperationStatus.SUCCESS,
                    success=True, message="ok",
                )
        registry = OperationRegistry()
        registry.register("backup", MockExecutor())
        registry.register("restore", MockExecutor())
        self.assertTrue(registry.supports("backup"))
        self.assertEqual(len(registry.list()), 2)


if __name__ == "__main__":
    unittest.main()
