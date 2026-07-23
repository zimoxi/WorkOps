"""
WorkOps Restore Execution Framework Tests
Sprint037: Restore Execution Framework

覆盖：
- RestoreExecutor contract
- RestoreResult validation
- RestoreExecutorRegistry
- RestoreRuntime contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.restore.executor import RestoreExecutor
from backup_manager.restore.result import RestoreResult
from backup_manager.restore.registry import RestoreExecutorRegistry
from backup_manager.restore.runtime import RestoreRuntime
from backup_manager.restore.execution import RestoreExecution
from backup_manager.restore.state import RestoreExecutionState
from backup_manager.restore.errors import (
    RestoreExecutorError,
    RestoreExecutorNotFoundError,
    RestoreExecutorAlreadyExistsError,
    RestoreWorkflowError,
)


# ============================================================================
# RestoreExecutor Contract
# ============================================================================

class TestRestoreExecutorContract(unittest.TestCase):
    """恢复执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(RestoreExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="restored")
        executor = MockExecutor()
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        result = executor.execute(execution)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadExecutor(RestoreExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# RestoreResult
# ============================================================================

class TestRestoreResult(unittest.TestCase):
    """恢复结果测试"""

    def test_valid_result(self):
        result = RestoreResult(success=True, message="done")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "done")

    def test_frozen(self):
        result = RestoreResult(success=True, message="ok")
        with self.assertRaises(AttributeError):
            result.success = False

    def test_slots(self):
        result = RestoreResult(success=True, message="ok")
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_success_must_be_bool(self):
        with self.assertRaises(RestoreExecutorError):
            RestoreResult(success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(RestoreExecutorError):
            RestoreResult(success=True, message=123)

    def test_started_at_must_be_datetime(self):
        with self.assertRaises(RestoreExecutorError):
            RestoreResult(success=True, message="ok", started_at="not_dt")

    def test_finished_at_must_be_datetime(self):
        with self.assertRaises(RestoreExecutorError):
            RestoreResult(success=True, message="ok", finished_at="not_dt")

    def test_with_timestamps(self):
        now = datetime.now(timezone.utc)
        result = RestoreResult(
            success=True, message="ok",
            started_at=now, finished_at=now,
        )
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.finished_at)

    def test_failed_result(self):
        result = RestoreResult(success=False, message="error")
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = RestoreResult(success=True, message="ok")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_repr_no_secrets(self):
        result = RestoreResult(success=True, message="ok")
        r = repr(result)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RestoreExecutorRegistry
# ============================================================================

class TestRestoreExecutorRegistry(unittest.TestCase):
    """恢复执行器注册表测试"""

    def setUp(self):
        self.registry = RestoreExecutorRegistry()

    def _make_executor(self):
        class MockExecutor(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        return MockExecutor()

    def test_register_and_get(self):
        executor = self._make_executor()
        self.registry.register("mock", executor)
        got = self.registry.get("mock")
        self.assertIs(got, executor)

    def test_duplicate_rejected(self):
        executor = self._make_executor()
        self.registry.register("mock", executor)
        with self.assertRaises(RestoreExecutorAlreadyExistsError):
            self.registry.register("mock", executor)

    def test_get_not_found(self):
        with self.assertRaises(RestoreExecutorNotFoundError):
            self.registry.get("nonexistent")

    def test_list(self):
        self.registry.register("mock1", self._make_executor())
        self.registry.register("mock2", self._make_executor())
        types = self.registry.list()
        self.assertEqual(len(types), 2)

    def test_supports_true(self):
        self.registry.register("mock", self._make_executor())
        self.assertTrue(self.registry.supports("mock"))

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
        with open("backup_manager/restore/registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("__import__", "import_module"):
                    self.fail("registry uses dynamic import")

    def test_list_empty(self):
        self.assertEqual(self.registry.list(), [])


# ============================================================================
# RestoreRuntime Contract
# ============================================================================

class TestRestoreRuntimeContract(unittest.TestCase):
    """恢复运行时契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreRuntime, ABC))

    def test_has_prepare(self):
        self.assertTrue(hasattr(RestoreRuntime, "prepare"))

    def test_has_execute(self):
        self.assertTrue(hasattr(RestoreRuntime, "execute"))

    def test_has_cleanup(self):
        self.assertTrue(hasattr(RestoreRuntime, "cleanup"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreRuntime()

    def test_concrete_subclass(self):
        class MockRuntime(RestoreRuntime):
            def prepare(self):
                pass
            def execute(self):
                return {"success": True}
            def cleanup(self):
                pass
        runtime = MockRuntime()
        runtime.prepare()
        result = runtime.execute()
        self.assertTrue(result["success"])
        runtime.cleanup()

    def test_missing_prepare(self):
        class BadRuntime(RestoreRuntime):
            def execute(self):
                return {}
            def cleanup(self):
                pass
        with self.assertRaises(TypeError):
            BadRuntime()

    def test_missing_execute(self):
        class BadRuntime(RestoreRuntime):
            def prepare(self):
                pass
            def cleanup(self):
                pass
        with self.assertRaises(TypeError):
            BadRuntime()

    def test_missing_cleanup(self):
        class BadRuntime(RestoreRuntime):
            def prepare(self):
                pass
            def execute(self):
                return {}
        with self.assertRaises(TypeError):
            BadRuntime()


# ============================================================================
# Error Model
# ============================================================================

class TestRestoreExecutorErrors(unittest.TestCase):
    """错误模型测试"""

    def test_executor_error(self):
        with self.assertRaises(RestoreWorkflowError):
            raise RestoreExecutorError("test")

    def test_not_found_error(self):
        exc = RestoreExecutorNotFoundError("rsync")
        self.assertIn("rsync", str(exc))

    def test_already_exists_error(self):
        exc = RestoreExecutorAlreadyExistsError("rsync")
        self.assertIn("rsync", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (RestoreExecutorError, ("test",)),
            (RestoreExecutorNotFoundError, ("test",)),
            (RestoreExecutorAlreadyExistsError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "command"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_result_no_credentials(self):
        result = RestoreResult(success=True, message="ok")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_registry_no_credentials(self):
        registry = RestoreExecutorRegistry()
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(registry, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["executor.py", "result.py", "registry.py", "runtime.py"]:
            filepath = os.path.join("backup_manager", "restore", filename)
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
        for filename in ["executor.py", "result.py", "registry.py", "runtime.py"]:
            filepath = os.path.join("backup_manager", "restore", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_registry_lifecycle(self):
        """完整注册表生命周期"""
        class MockExecutor(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        registry = RestoreExecutorRegistry()
        registry.register("mock", MockExecutor())
        self.assertTrue(registry.supports("mock"))
        self.assertEqual(len(registry.list()), 1)
        got = registry.get("mock")
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        result = got.execute(execution)
        self.assertTrue(result.success)

    def test_executor_returns_failed_result(self):
        class FailExecutor(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=False, message="failed")
        executor = FailExecutor()
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        result = executor.execute(execution)
        self.assertFalse(result.success)

    def test_result_repr_no_secrets(self):
        result = RestoreResult(success=True, message="ok")
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# Extended Tests
# ============================================================================

class TestRestoreExecutorExtended(unittest.TestCase):
    """恢复执行器扩展测试"""

    def test_executor_with_timestamps(self):
        class TimedExecutor(RestoreExecutor):
            def execute(self, execution):
                now = datetime.now(timezone.utc)
                return RestoreResult(
                    success=True, message="ok",
                    started_at=now, finished_at=now,
                )
        executor = TimedExecutor()
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        result = executor.execute(execution)
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.finished_at)

    def test_multiple_registrations(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        registry = RestoreExecutorRegistry()
        for i in range(5):
            registry.register(f"executor-{i}", E())
        self.assertEqual(len(registry.list()), 5)

    def test_get_returns_same_instance(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        registry = RestoreExecutorRegistry()
        executor = E()
        registry.register("test", executor)
        self.assertIs(registry.get("test"), executor)

    def test_result_error_no_secrets(self):
        try:
            raise RestoreExecutorError("test error")
        except RestoreExecutorError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_registry_error_no_secrets(self):
        try:
            raise RestoreExecutorNotFoundError("test")
        except RestoreExecutorNotFoundError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_executor_type_property(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        registry = RestoreExecutorRegistry()
        registry.register("rsync", E())
        registry.register("borg", E())
        self.assertIn("rsync", registry.list())
        self.assertIn("borg", registry.list())

    def test_registry_empty_type_whitespace_rejected(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        registry = RestoreExecutorRegistry()
        with self.assertRaises(TypeError):
            registry.register("   ", E())

    def test_result_success_true_false(self):
        r1 = RestoreResult(success=True, message="ok")
        r2 = RestoreResult(success=False, message="fail")
        self.assertTrue(r1.success)
        self.assertFalse(r2.success)

    def test_result_empty_message(self):
        result = RestoreResult(success=True, message="")
        self.assertEqual(result.message, "")

    def test_executor_execute_returns_result(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        e = E()
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        result = e.execute(execution)
        self.assertIsInstance(result, RestoreResult)

    def test_registry_supports_after_register(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        registry = RestoreExecutorRegistry()
        self.assertFalse(registry.supports("test"))
        registry.register("test", E())
        self.assertTrue(registry.supports("test"))

    def test_executor_with_pending_execution(self):
        class E(RestoreExecutor):
            def execute(self, execution):
                return RestoreResult(success=True, message="ok")
        e = E()
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        self.assertEqual(execution.state, RestoreExecutionState.PENDING)
        result = e.execute(execution)
        self.assertTrue(result.success)

    def test_runtime_lifecycle(self):
        class MockRuntime(RestoreRuntime):
            def __init__(self):
                self._prepared = False
            def prepare(self):
                self._prepared = True
            def execute(self):
                return {"success": True}
            def cleanup(self):
                self._prepared = False
        runtime = MockRuntime()
        runtime.prepare()
        self.assertTrue(runtime._prepared)
        result = runtime.execute()
        self.assertTrue(result["success"])
        runtime.cleanup()
        self.assertFalse(runtime._prepared)

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(RestoreExecutorError, RestoreWorkflowError))
        self.assertTrue(issubclass(RestoreExecutorNotFoundError, RestoreWorkflowError))
        self.assertTrue(issubclass(RestoreExecutorAlreadyExistsError, RestoreWorkflowError))


if __name__ == "__main__":
    unittest.main()
