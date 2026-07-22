"""
WorkOps Backup Executor Framework Tests
Sprint031: Backup Executor Framework

覆盖：
- BackupExecutor contract
- ExecutorResult validation
- BackupExecutorRegistry
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.backup.executor import BackupExecutor
from backup_manager.backup.executor_result import ExecutorResult
from backup_manager.backup.executor_registry import BackupExecutorRegistry
from backup_manager.backup.execution import BackupExecution
from backup_manager.backup.state import BackupExecutionState
from backup_manager.backup.errors import (
    BackupExecutorError,
    ExecutorNotFoundError,
    ExecutorAlreadyExistsError,
    BackupWorkflowError,
)


# ============================================================================
# BackupExecutor Contract
# ============================================================================

class TestBackupExecutorContract(unittest.TestCase):
    """执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(BackupExecutor, ABC))

    def test_has_execute_method(self):
        self.assertTrue(hasattr(BackupExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            BackupExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(
                    success=True,
                    message="mock done",
                    started_at=datetime.now(timezone.utc),
                    finished_at=datetime.now(timezone.utc),
                )
        executor = MockExecutor()
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "mock done")

    def test_missing_execute_method(self):
        class BadExecutor(BackupExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()

    def test_executor_with_registry(self):
        class MockExecutor(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        registry = BackupExecutorRegistry()
        registry.register("mock", MockExecutor())
        got = registry.get("mock")
        self.assertIsInstance(got, BackupExecutor)


# ============================================================================
# ExecutorResult
# ============================================================================

class TestExecutorResult(unittest.TestCase):
    """执行结果测试"""

    def test_valid_result(self):
        result = ExecutorResult(success=True, message="done")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "done")
        self.assertIsNone(result.started_at)
        self.assertIsNone(result.finished_at)

    def test_frozen(self):
        result = ExecutorResult(success=True, message="ok")
        with self.assertRaises(AttributeError):
            result.success = False

    def test_slots(self):
        result = ExecutorResult(success=True, message="ok")
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_success_must_be_bool(self):
        with self.assertRaises(BackupExecutorError):
            ExecutorResult(success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(BackupExecutorError):
            ExecutorResult(success=True, message=123)

    def test_started_at_must_be_datetime(self):
        with self.assertRaises(BackupExecutorError):
            ExecutorResult(success=True, message="ok", started_at="not_dt")

    def test_finished_at_must_be_datetime(self):
        with self.assertRaises(BackupExecutorError):
            ExecutorResult(success=True, message="ok", finished_at="not_dt")

    def test_with_timestamps(self):
        now = datetime.now(timezone.utc)
        result = ExecutorResult(
            success=True, message="ok",
            started_at=now, finished_at=now,
        )
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.finished_at)

    def test_failed_result(self):
        result = ExecutorResult(success=False, message="error")
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = ExecutorResult(success=True, message="ok")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_repr_no_secrets(self):
        result = ExecutorResult(success=True, message="ok")
        r = repr(result)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# BackupExecutorRegistry
# ============================================================================

class TestBackupExecutorRegistry(unittest.TestCase):
    """执行器注册表测试"""

    def setUp(self):
        self.registry = BackupExecutorRegistry()

    def _make_executor(self):
        class MockExecutor(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        return MockExecutor()

    def test_register_and_get(self):
        executor = self._make_executor()
        self.registry.register("mock", executor)
        got = self.registry.get("mock")
        self.assertIs(got, executor)

    def test_duplicate_rejected(self):
        executor = self._make_executor()
        self.registry.register("mock", executor)
        with self.assertRaises(ExecutorAlreadyExistsError):
            self.registry.register("mock", executor)

    def test_get_not_found(self):
        with self.assertRaises(ExecutorNotFoundError):
            self.registry.get("nonexistent")

    def test_list(self):
        self.registry.register("mock1", self._make_executor())
        self.registry.register("mock2", self._make_executor())
        types = self.registry.list()
        self.assertEqual(len(types), 2)
        self.assertIn("mock1", types)
        self.assertIn("mock2", types)

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
        with open("backup_manager/backup/executor_registry.py") as f:
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

class TestBackupExecutorErrors(unittest.TestCase):
    """错误模型测试"""

    def test_executor_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise BackupExecutorError("test")

    def test_not_found_error(self):
        exc = ExecutorNotFoundError("rsync")
        self.assertIn("rsync", str(exc))

    def test_already_exists_error(self):
        exc = ExecutorAlreadyExistsError("rsync")
        self.assertIn("rsync", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (BackupExecutorError, ("test",)),
            (ExecutorNotFoundError, ("test",)),
            (ExecutorAlreadyExistsError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "command"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_executor_result_no_credentials(self):
        result = ExecutorResult(success=True, message="ok")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_registry_no_credentials(self):
        registry = BackupExecutorRegistry()
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(registry, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["executor.py", "executor_result.py", "executor_registry.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
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
        for filename in ["executor.py", "executor_result.py", "executor_registry.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_result_repr_no_secrets(self):
        result = ExecutorResult(success=True, message="ok")
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_registry_lifecycle(self):
        """完整注册表生命周期"""
        class E1(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="e1")
        class E2(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=False, message="e2")
        registry = BackupExecutorRegistry()
        registry.register("e1", E1())
        registry.register("e2", E2())
        self.assertEqual(len(registry.list()), 2)
        self.assertTrue(registry.supports("e1"))
        self.assertTrue(registry.supports("e2"))
        self.assertFalse(registry.supports("e3"))


# ============================================================================
# Additional Executor Tests
# ============================================================================

class TestBackupExecutorExtended(unittest.TestCase):
    """执行器扩展测试"""

    def test_executor_returns_failed_result(self):
        class FailExecutor(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=False, message="failed")
        executor = FailExecutor()
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertFalse(result.success)

    def test_executor_with_timestamps(self):
        class TimedExecutor(BackupExecutor):
            def execute(self, execution):
                now = datetime.now(timezone.utc)
                return ExecutorResult(
                    success=True, message="ok",
                    started_at=now, finished_at=now,
                )
        executor = TimedExecutor()
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertIsNotNone(result.started_at)
        self.assertIsNotNone(result.finished_at)

    def test_multiple_registrations(self):
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        registry = BackupExecutorRegistry()
        for i in range(5):
            registry.register(f"executor-{i}", E())
        self.assertEqual(len(registry.list()), 5)

    def test_get_returns_same_instance(self):
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        registry = BackupExecutorRegistry()
        executor = E()
        registry.register("test", executor)
        self.assertIs(registry.get("test"), executor)

    def test_result_error_no_secrets(self):
        try:
            raise BackupExecutorError("test error")
        except BackupExecutorError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_registry_error_no_secrets(self):
        try:
            raise ExecutorNotFoundError("test")
        except ExecutorNotFoundError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_executor_type_property(self):
        """执行器类型通过注册表键标识"""
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        registry = BackupExecutorRegistry()
        registry.register("rsync", E())
        registry.register("borg", E())
        self.assertIn("rsync", registry.list())
        self.assertIn("borg", registry.list())

    def test_registry_empty_type_whitespace_rejected(self):
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        registry = BackupExecutorRegistry()
        with self.assertRaises(TypeError):
            registry.register("   ", E())

    def test_result_success_true_false(self):
        r1 = ExecutorResult(success=True, message="ok")
        r2 = ExecutorResult(success=False, message="fail")
        self.assertTrue(r1.success)
        self.assertFalse(r2.success)

    def test_result_empty_message(self):
        result = ExecutorResult(success=True, message="")
        self.assertEqual(result.message, "")

    def test_executor_execute_returns_result(self):
        """execute 必须返回 ExecutorResult"""
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        e = E()
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = e.execute(execution)
        self.assertIsInstance(result, ExecutorResult)

    def test_registry_supports_after_register(self):
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        registry = BackupExecutorRegistry()
        self.assertFalse(registry.supports("test"))
        registry.register("test", E())
        self.assertTrue(registry.supports("test"))

    def test_executor_with_pending_execution(self):
        """执行器可以接收 PENDING 状态的执行"""
        class E(BackupExecutor):
            def execute(self, execution):
                return ExecutorResult(success=True, message="ok")
        e = E()
        execution = BackupExecution(execution_id="e1", job_id="j1")
        self.assertEqual(execution.state, BackupExecutionState.PENDING)
        result = e.execute(execution)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
