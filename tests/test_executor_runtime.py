"""
WorkOps Safe Executor Runtime Tests
Sprint032: Safe Executor Runtime

覆盖：
- ExecutionContext validation
- ExecutorRuntime contract
- ExecutionResultCollector lifecycle
- ExecutionTimeout validation
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.backup.runtime import ExecutionContext
from backup_manager.backup.runtime_executor import ExecutorRuntime
from backup_manager.backup.result_collector import ExecutionResultCollector
from backup_manager.backup.timeout import ExecutionTimeout
from backup_manager.backup.executor_result import ExecutorResult
from backup_manager.backup.errors import (
    ExecutorRuntimeError,
    ExecutionTimeoutError,
    BackupWorkflowError,
)


# ============================================================================
# ExecutionContext
# ============================================================================

class TestExecutionContext(unittest.TestCase):
    """执行上下文测试"""

    def test_valid_context(self):
        ctx = ExecutionContext(execution_id="e1")
        self.assertEqual(ctx.execution_id, "e1")
        self.assertEqual(ctx.timeout_seconds, 300)
        self.assertIsNotNone(ctx.created_at)
        self.assertEqual(ctx.metadata, ())

    def test_frozen(self):
        ctx = ExecutionContext(execution_id="e1")
        with self.assertRaises(AttributeError):
            ctx.execution_id = "other"

    def test_slots(self):
        ctx = ExecutionContext(execution_id="e1")
        with self.assertRaises(AttributeError):
            ctx.__dict__

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="")

    def test_whitespace_execution_id_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="   ")

    def test_timeout_must_be_int(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="e1", timeout_seconds="300")

    def test_timeout_must_be_positive(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="e1", timeout_seconds=0)

    def test_timeout_negative_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="e1", timeout_seconds=-1)

    def test_timeout_bool_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="e1", timeout_seconds=True)

    def test_custom_timeout(self):
        ctx = ExecutionContext(execution_id="e1", timeout_seconds=60)
        self.assertEqual(ctx.timeout_seconds, 60)

    def test_metadata_must_be_tuple(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionContext(execution_id="e1", metadata=["not", "tuple"])

    def test_metadata_allowed(self):
        ctx = ExecutionContext(execution_id="e1", metadata=("key", "value"))
        self.assertEqual(ctx.metadata, ("key", "value"))

    def test_timezone_aware(self):
        ctx = ExecutionContext(execution_id="e1")
        self.assertIsNotNone(ctx.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        ctx = ExecutionContext(execution_id="e1")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(ctx, attr))

    def test_repr_no_secrets(self):
        ctx = ExecutionContext(execution_id="e1")
        r = repr(ctx)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# ExecutorRuntime Contract
# ============================================================================

class TestExecutorRuntimeContract(unittest.TestCase):
    """运行时契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(ExecutorRuntime, ABC))

    def test_has_prepare(self):
        self.assertTrue(hasattr(ExecutorRuntime, "prepare"))

    def test_has_collect(self):
        self.assertTrue(hasattr(ExecutorRuntime, "collect"))

    def test_has_cleanup(self):
        self.assertTrue(hasattr(ExecutorRuntime, "cleanup"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ExecutorRuntime()

    def test_concrete_subclass(self):
        class MockRuntime(ExecutorRuntime):
            def __init__(self):
                self._prepared = False
                self._result = {}
            def prepare(self, context):
                self._prepared = True
            def collect(self):
                return self._result
            def cleanup(self):
                self._prepared = False
        runtime = MockRuntime()
        ctx = ExecutionContext(execution_id="e1")
        runtime.prepare(ctx)
        self.assertTrue(runtime._prepared)
        result = runtime.collect()
        self.assertIsInstance(result, dict)
        runtime.cleanup()
        self.assertFalse(runtime._prepared)

    def test_missing_prepare(self):
        class BadRuntime(ExecutorRuntime):
            def collect(self):
                return {}
            def cleanup(self):
                pass
        with self.assertRaises(TypeError):
            BadRuntime()

    def test_missing_collect(self):
        class BadRuntime(ExecutorRuntime):
            def prepare(self, context):
                pass
            def cleanup(self):
                pass
        with self.assertRaises(TypeError):
            BadRuntime()

    def test_missing_cleanup(self):
        class BadRuntime(ExecutorRuntime):
            def prepare(self, context):
                pass
            def collect(self):
                return {}
        with self.assertRaises(TypeError):
            BadRuntime()


# ============================================================================
# ExecutionResultCollector
# ============================================================================

class TestExecutionResultCollector(unittest.TestCase):
    """结果收集器测试"""

    def setUp(self):
        self.collector = ExecutionResultCollector()

    def test_collect_and_get(self):
        result = ExecutorResult(success=True, message="ok")
        self.collector.collect_result("e1", result)
        got = self.collector.get_result("e1")
        self.assertIs(got, result)

    def test_get_not_found(self):
        with self.assertRaises(ExecutorRuntimeError):
            self.collector.get_result("nonexistent")

    def test_has_result(self):
        self.assertFalse(self.collector.has_result("e1"))
        self.collector.collect_result("e1", ExecutorResult(success=True, message="ok"))
        self.assertTrue(self.collector.has_result("e1"))

    def test_list_results(self):
        self.collector.collect_result("e1", ExecutorResult(success=True, message="ok"))
        self.collector.collect_result("e2", ExecutorResult(success=False, message="fail"))
        ids = self.collector.list_results()
        self.assertEqual(len(ids), 2)
        self.assertIn("e1", ids)
        self.assertIn("e2", ids)

    def test_clear(self):
        self.collector.collect_result("e1", ExecutorResult(success=True, message="ok"))
        self.collector.clear()
        self.assertEqual(len(self.collector.list_results()), 0)

    def test_overwrite_result(self):
        r1 = ExecutorResult(success=True, message="first")
        r2 = ExecutorResult(success=False, message="second")
        self.collector.collect_result("e1", r1)
        self.collector.collect_result("e1", r2)
        got = self.collector.get_result("e1")
        self.assertEqual(got.message, "second")

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            self.collector.collect_result("", ExecutorResult(success=True, message="ok"))

    def test_non_result_rejected(self):
        with self.assertRaises(TypeError):
            self.collector.collect_result("e1", "not_a_result")

    def test_list_empty(self):
        self.assertEqual(self.collector.list_results(), [])

    def test_no_forbidden_fields(self):
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(self.collector, attr))


# ============================================================================
# ExecutionTimeout
# ============================================================================

class TestExecutionTimeout(unittest.TestCase):
    """超时模型测试"""

    def test_valid_timeout(self):
        timeout = ExecutionTimeout(300)
        self.assertEqual(timeout.timeout_seconds, 300)

    def test_zero_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionTimeout(0)

    def test_negative_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionTimeout(-1)

    def test_must_be_int(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionTimeout("300")

    def test_bool_rejected(self):
        with self.assertRaises(ExecutorRuntimeError):
            ExecutionTimeout(True)

    def test_repr(self):
        timeout = ExecutionTimeout(60)
        self.assertIn("60", repr(timeout))

    def test_no_forbidden_fields(self):
        timeout = ExecutionTimeout(300)
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(timeout, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestExecutorRuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_runtime_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise ExecutorRuntimeError("test")

    def test_timeout_error(self):
        exc = ExecutionTimeoutError("e1")
        self.assertIn("e1", str(exc))

    def test_timeout_error_no_id(self):
        exc = ExecutionTimeoutError()
        self.assertIn("timed out", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (ExecutorRuntimeError, ("test",)),
            (ExecutionTimeoutError, ("e1",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "command"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_context_no_credentials(self):
        ctx = ExecutionContext(execution_id="e1")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(ctx, attr))

    def test_collector_no_credentials(self):
        collector = ExecutionResultCollector()
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(collector, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["runtime.py", "runtime_executor.py", "result_collector.py", "timeout.py"]:
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
        for filename in ["runtime.py", "runtime_executor.py", "result_collector.py", "timeout.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_collector_repr_no_secrets(self):
        collector = ExecutionResultCollector()
        r = repr(collector)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


if __name__ == "__main__":
    unittest.main()
