"""
WorkOps Health Runtime Integration Tests
Sprint055: Health Runtime Integration Foundation

覆盖：
- HealthExecutionStatus enum
- HealthExecutionRequest validation
- HealthExecutionResult validation
- HealthExecutor contract
- HealthRuntimePipeline contract
- validate_health_execution_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.health_runtime.model import HealthExecutionStatus
from backup_manager.health_runtime.request import HealthExecutionRequest
from backup_manager.health_runtime.result import HealthExecutionResult
from backup_manager.health_runtime.executor import HealthExecutor
from backup_manager.health_runtime.pipeline import HealthRuntimePipeline, validate_health_execution_request
from backup_manager.health_runtime.errors import (
    HealthRuntimeError,
    InvalidHealthExecutionRequestError,
    HealthRuntimeConflictError,
    HealthRuntimeUnavailableError,
)


# ============================================================================
# HealthExecutionStatus
# ============================================================================

class TestHealthExecutionStatus(unittest.TestCase):
    """健康执行状态测试"""

    def test_created(self):
        self.assertEqual(HealthExecutionStatus.CREATED.value, "created")

    def test_running(self):
        self.assertEqual(HealthExecutionStatus.RUNNING.value, "running")

    def test_completed(self):
        self.assertEqual(HealthExecutionStatus.COMPLETED.value, "completed")

    def test_failed(self):
        self.assertEqual(HealthExecutionStatus.FAILED.value, "failed")

    def test_four_statuses(self):
        self.assertEqual(len(HealthExecutionStatus), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            HealthExecutionStatus("nonexistent")


# ============================================================================
# HealthExecutionRequest
# ============================================================================

class TestHealthExecutionRequest(unittest.TestCase):
    """健康执行请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "health_id": "h-001",
            "operation_id": "op-001",
            "execution_id": "exec-001",
            "adapter_id": "linux-001",
            "device_id": "dev-001",
        }
        defaults.update(kwargs)
        return HealthExecutionRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.health_id, "h-001")
        self.assertEqual(req.operation_id, "op-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.device_id, "dev-001")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.health_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_health_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            self._make_request(health_id="")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            self._make_request(operation_id="")

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            self._make_request(execution_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            self._make_request(adapter_id="")

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            self._make_request(device_id="")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# HealthExecutionResult
# ============================================================================

class TestHealthExecutionResult(unittest.TestCase):
    """健康执行结果测试"""

    def test_valid_result(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        self.assertEqual(result.health_id, "h-001")
        self.assertTrue(result.healthy)
        self.assertEqual(result.status, HealthExecutionStatus.COMPLETED)

    def test_frozen(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.health_id = "other"

    def test_slots(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_health_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            HealthExecutionResult(
                health_id="", status=HealthExecutionStatus.COMPLETED,
                healthy=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            HealthExecutionResult(
                health_id="h-001", status="completed",
                healthy=True, message="ok",
            )

    def test_healthy_must_be_bool(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            HealthExecutionResult(
                health_id="h-001", status=HealthExecutionStatus.COMPLETED,
                healthy=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            HealthExecutionResult(
                health_id="h-001", status=HealthExecutionStatus.COMPLETED,
                healthy=True, message=123,
            )

    def test_timezone_aware(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_all_statuses(self):
        for status in HealthExecutionStatus:
            result = HealthExecutionResult(
                health_id="h-001", status=status,
                healthy=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_no_forbidden_fields(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_unhealthy_result(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=False, message="disk full",
        )
        self.assertFalse(result.healthy)


# ============================================================================
# HealthExecutor Contract
# ============================================================================

class TestHealthExecutorContract(unittest.TestCase):
    """健康执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(HealthExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(HealthExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            HealthExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(HealthExecutor):
            def execute(self, request):
                return HealthExecutionResult(
                    health_id=request.health_id,
                    status=HealthExecutionStatus.COMPLETED,
                    healthy=True, message="ok",
                )
        executor = MockExecutor()
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        result = executor.execute(req)
        self.assertTrue(result.healthy)

    def test_missing_execute(self):
        class BadExecutor(HealthExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# HealthRuntimePipeline Contract
# ============================================================================

class TestHealthRuntimePipelineContract(unittest.TestCase):
    """健康运行时管道契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(HealthRuntimePipeline, ABC))

    def test_has_prepare(self):
        self.assertTrue(hasattr(HealthRuntimePipeline, "prepare"))

    def test_has_execute(self):
        self.assertTrue(hasattr(HealthRuntimePipeline, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            HealthRuntimePipeline()

    def test_concrete_subclass(self):
        class MockPipeline(HealthRuntimePipeline):
            def prepare(self, request):
                pass
            def execute(self, request):
                return HealthExecutionResult(
                    health_id=request.health_id,
                    status=HealthExecutionStatus.COMPLETED,
                    healthy=True, message="ok",
                )
        pipeline = MockPipeline()
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        pipeline.prepare(req)
        result = pipeline.execute(req)
        self.assertTrue(result.healthy)

    def test_missing_prepare(self):
        class BadPipeline(HealthRuntimePipeline):
            def execute(self, request):
                pass
        with self.assertRaises(TypeError):
            BadPipeline()

    def test_missing_execute(self):
        class BadPipeline(HealthRuntimePipeline):
            def prepare(self, request):
                pass
        with self.assertRaises(TypeError):
            BadPipeline()


# ============================================================================
# validate_health_execution_request
# ============================================================================

class TestValidateHealthExecutionRequest(unittest.TestCase):
    """验证健康执行请求测试"""

    def test_valid_request(self):
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        validate_health_execution_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            validate_health_execution_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestHealthRuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_runtime_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise HealthRuntimeError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise InvalidHealthExecutionRequestError("test")

    def test_conflict_error(self):
        exc = HealthRuntimeConflictError("h-001")
        self.assertIn("h-001", str(exc))

    def test_unavailable_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise HealthRuntimeUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (HealthRuntimeError, ("test",)),
            (InvalidHealthExecutionRequestError, ("test",)),
            (HealthRuntimeConflictError, ("h-001",)),
            (HealthRuntimeUnavailableError, ("test",)),
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
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        hr_dir = os.path.join("backup_manager", "health_runtime")
        for filename in os.listdir(hr_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(hr_dir, filename)
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
        hr_dir = os.path.join("backup_manager", "health_runtime")
        for filename in os.listdir(hr_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(hr_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_pipeline_lifecycle(self):
        """完整管道生命周期"""
        class MockPipeline(HealthRuntimePipeline):
            def prepare(self, request):
                pass
            def execute(self, request):
                return HealthExecutionResult(
                    health_id=request.health_id,
                    status=HealthExecutionStatus.COMPLETED,
                    healthy=True, message="ok",
                )
        pipeline = MockPipeline()
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        pipeline.prepare(req)
        result = pipeline.execute(req)
        self.assertTrue(result.healthy)
        self.assertEqual(result.status, HealthExecutionStatus.COMPLETED)


# ============================================================================
# Extended Tests
# ============================================================================

class TestHealthRuntimeExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidHealthExecutionRequestError, HealthRuntimeError))
        self.assertTrue(issubclass(HealthRuntimeConflictError, HealthRuntimeError))
        self.assertTrue(issubclass(HealthRuntimeUnavailableError, HealthRuntimeError))

    def test_request_repr_no_secrets(self):
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_preserves_all_fields(self):
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        self.assertEqual(req.health_id, "h-001")
        self.assertEqual(req.operation_id, "op-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.device_id, "dev-001")

    def test_executor_returns_result(self):
        class MockExecutor(HealthExecutor):
            def execute(self, request):
                return HealthExecutionResult(
                    health_id=request.health_id,
                    status=HealthExecutionStatus.COMPLETED,
                    healthy=True, message="ok",
                )
        executor = MockExecutor()
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        result = executor.execute(req)
        self.assertIsInstance(result, HealthExecutionResult)

    def test_pipeline_prepare_then_execute(self):
        class MockPipeline(HealthRuntimePipeline):
            def __init__(self):
                self.prepared = False
            def prepare(self, request):
                self.prepared = True
            def execute(self, request):
                return HealthExecutionResult(
                    health_id=request.health_id,
                    status=HealthExecutionStatus.COMPLETED,
                    healthy=self.prepared, message="ok" if self.prepared else "not prepared",
                )
        pipeline = MockPipeline()
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        pipeline.prepare(req)
        result = pipeline.execute(req)
        self.assertTrue(result.healthy)

    def test_error_messages_safe(self):
        try:
            raise HealthRuntimeError("test")
        except HealthRuntimeError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_conflict_error_message(self):
        exc = HealthRuntimeConflictError("test-health")
        self.assertIn("test-health", str(exc))

    def test_unavailable_error_message(self):
        exc = HealthRuntimeUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            HealthExecutionRequest(
                health_id="   ", operation_id="op-001",
                execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
            )

    def test_result_empty_message_accepted(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="",
        )
        self.assertEqual(result.message, "")

    def test_request_no_command(self):
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        self.assertFalse(hasattr(req, "command"))

    def test_result_no_stderr(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.COMPLETED,
            healthy=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))

    def test_result_all_statuses(self):
        for status in HealthExecutionStatus:
            result = HealthExecutionResult(
                health_id="h-001", status=status,
                healthy=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_pipeline_returns_result(self):
        class MockPipeline(HealthRuntimePipeline):
            def prepare(self, request):
                pass
            def execute(self, request):
                return HealthExecutionResult(
                    health_id=request.health_id,
                    status=HealthExecutionStatus.COMPLETED,
                    healthy=True, message="ok",
                )
        pipeline = MockPipeline()
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        result = pipeline.execute(req)
        self.assertIsInstance(result, HealthExecutionResult)

    def test_request_whitespace_device_id_rejected(self):
        with self.assertRaises(InvalidHealthExecutionRequestError):
            HealthExecutionRequest(
                health_id="h-001", operation_id="op-001",
                execution_id="exec-001", adapter_id="linux-001", device_id="   ",
            )

    def test_failed_result(self):
        result = HealthExecutionResult(
            health_id="h-001", status=HealthExecutionStatus.FAILED,
            healthy=False, message="error",
        )
        self.assertFalse(result.healthy)
        self.assertEqual(result.status, HealthExecutionStatus.FAILED)

    def test_request_no_ssh(self):
        req = HealthExecutionRequest(
            health_id="h-001", operation_id="op-001",
            execution_id="exec-001", adapter_id="linux-001", device_id="dev-001",
        )
        self.assertFalse(hasattr(req, "ssh"))


if __name__ == "__main__":
    unittest.main()
