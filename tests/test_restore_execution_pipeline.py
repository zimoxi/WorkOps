"""
WorkOps Restore Execution Pipeline Tests
Sprint054: Restore Execution Pipeline Foundation

覆盖：
- RestoreExecutionStatus enum
- RestoreExecutionRequest validation
- RestoreExecutionResult validation
- RestoreExecutor contract
- RestoreExecutionPipeline contract
- validate_restore_execution_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.restore_execution.model import (
    RestoreExecutionStatus,
    RestoreExecutionRequest,
    validate_restore_execution_request,
)
from backup_manager.restore_execution.result import RestoreExecutionResult
from backup_manager.restore_execution.executor import RestoreExecutor
from backup_manager.restore_execution.pipeline import RestoreExecutionPipeline
from backup_manager.restore_execution.errors import (
    RestoreExecutionError,
    InvalidRestoreExecutionRequestError,
    RestoreExecutionConflictError,
    RestoreExecutionUnavailableError,
)


# ============================================================================
# RestoreExecutionStatus
# ============================================================================

class TestRestoreExecutionStatus(unittest.TestCase):
    """恢复执行状态测试"""

    def test_created(self):
        self.assertEqual(RestoreExecutionStatus.CREATED.value, "created")

    def test_preparing(self):
        self.assertEqual(RestoreExecutionStatus.PREPARING.value, "preparing")

    def test_running(self):
        self.assertEqual(RestoreExecutionStatus.RUNNING.value, "running")

    def test_completed(self):
        self.assertEqual(RestoreExecutionStatus.COMPLETED.value, "completed")

    def test_failed(self):
        self.assertEqual(RestoreExecutionStatus.FAILED.value, "failed")

    def test_five_statuses(self):
        self.assertEqual(len(RestoreExecutionStatus), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RestoreExecutionStatus("nonexistent")


# ============================================================================
# RestoreExecutionRequest
# ============================================================================

class TestRestoreExecutionRequest(unittest.TestCase):
    """恢复执行请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "restore_id": "r-001",
            "operation_id": "op-001",
            "job_id": "j-001",
            "execution_id": "exec-001",
            "adapter_id": "linux-001",
            "backup_id": "b-001",
        }
        defaults.update(kwargs)
        return RestoreExecutionRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.restore_id, "r-001")
        self.assertEqual(req.operation_id, "op-001")
        self.assertEqual(req.job_id, "j-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.backup_id, "b-001")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.restore_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            self._make_request(restore_id="")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            self._make_request(operation_id="")

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            self._make_request(job_id="")

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            self._make_request(execution_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            self._make_request(adapter_id="")

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            self._make_request(backup_id="")

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
# RestoreExecutionResult
# ============================================================================

class TestRestoreExecutionResult(unittest.TestCase):
    """恢复执行结果测试"""

    def test_valid_result(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertEqual(result.restore_id, "r-001")
        self.assertTrue(result.success)
        self.assertEqual(result.status, RestoreExecutionStatus.COMPLETED)

    def test_frozen(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.restore_id = "other"

    def test_slots(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            RestoreExecutionResult(
                restore_id="", status=RestoreExecutionStatus.COMPLETED,
                success=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            RestoreExecutionResult(
                restore_id="r-001", status="completed",
                success=True, message="ok",
            )

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            RestoreExecutionResult(
                restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
                success=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            RestoreExecutionResult(
                restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
                success=True, message=123,
            )

    def test_timezone_aware(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_all_statuses(self):
        for status in RestoreExecutionStatus:
            result = RestoreExecutionResult(
                restore_id="r-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_no_forbidden_fields(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_failed_result(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.FAILED,
            success=False, message="error",
        )
        self.assertFalse(result.success)
        self.assertEqual(result.status, RestoreExecutionStatus.FAILED)


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
            def execute(self, request):
                return RestoreExecutionResult(
                    restore_id=request.restore_id,
                    status=RestoreExecutionStatus.COMPLETED,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadExecutor(RestoreExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# RestoreExecutionPipeline Contract
# ============================================================================

class TestRestoreExecutionPipelineContract(unittest.TestCase):
    """恢复执行管道契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreExecutionPipeline, ABC))

    def test_has_prepare(self):
        self.assertTrue(hasattr(RestoreExecutionPipeline, "prepare"))

    def test_has_execute(self):
        self.assertTrue(hasattr(RestoreExecutionPipeline, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreExecutionPipeline()

    def test_concrete_subclass(self):
        class MockPipeline(RestoreExecutionPipeline):
            def prepare(self, request):
                pass
            def execute(self, request):
                return RestoreExecutionResult(
                    restore_id=request.restore_id,
                    status=RestoreExecutionStatus.COMPLETED,
                    success=True, message="ok",
                )
        pipeline = MockPipeline()
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        pipeline.prepare(req)
        result = pipeline.execute(req)
        self.assertTrue(result.success)

    def test_missing_prepare(self):
        class BadPipeline(RestoreExecutionPipeline):
            def execute(self, request):
                pass
        with self.assertRaises(TypeError):
            BadPipeline()

    def test_missing_execute(self):
        class BadPipeline(RestoreExecutionPipeline):
            def prepare(self, request):
                pass
        with self.assertRaises(TypeError):
            BadPipeline()


# ============================================================================
# validate_restore_execution_request
# ============================================================================

class TestValidateRestoreExecutionRequest(unittest.TestCase):
    """验证恢复执行请求测试"""

    def test_valid_request(self):
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        validate_restore_execution_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            validate_restore_execution_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestRestoreExecutionErrors(unittest.TestCase):
    """错误模型测试"""

    def test_execution_error(self):
        with self.assertRaises(RestoreExecutionError):
            raise RestoreExecutionError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(RestoreExecutionError):
            raise InvalidRestoreExecutionRequestError("test")

    def test_conflict_error(self):
        exc = RestoreExecutionConflictError("r-001")
        self.assertIn("r-001", str(exc))

    def test_unavailable_error(self):
        with self.assertRaises(RestoreExecutionError):
            raise RestoreExecutionUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (RestoreExecutionError, ("test",)),
            (InvalidRestoreExecutionRequestError, ("test",)),
            (RestoreExecutionConflictError, ("r-001",)),
            (RestoreExecutionUnavailableError, ("test",)),
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
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        re_dir = os.path.join("backup_manager", "restore_execution")
        for filename in os.listdir(re_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(re_dir, filename)
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
        re_dir = os.path.join("backup_manager", "restore_execution")
        for filename in os.listdir(re_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(re_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_pipeline_lifecycle(self):
        """完整管道生命周期"""
        class MockPipeline(RestoreExecutionPipeline):
            def prepare(self, request):
                pass
            def execute(self, request):
                return RestoreExecutionResult(
                    restore_id=request.restore_id,
                    status=RestoreExecutionStatus.COMPLETED,
                    success=True, message="ok",
                )
        pipeline = MockPipeline()
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        pipeline.prepare(req)
        result = pipeline.execute(req)
        self.assertTrue(result.success)
        self.assertEqual(result.status, RestoreExecutionStatus.COMPLETED)


# ============================================================================
# Extended Tests
# ============================================================================

class TestRestoreExecutionExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidRestoreExecutionRequestError, RestoreExecutionError))
        self.assertTrue(issubclass(RestoreExecutionConflictError, RestoreExecutionError))
        self.assertTrue(issubclass(RestoreExecutionUnavailableError, RestoreExecutionError))

    def test_request_repr_no_secrets(self):
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_preserves_all_fields(self):
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        self.assertEqual(req.restore_id, "r-001")
        self.assertEqual(req.operation_id, "op-001")
        self.assertEqual(req.job_id, "j-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.backup_id, "b-001")

    def test_executor_returns_result(self):
        class MockExecutor(RestoreExecutor):
            def execute(self, request):
                return RestoreExecutionResult(
                    restore_id=request.restore_id,
                    status=RestoreExecutionStatus.COMPLETED,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        result = executor.execute(req)
        self.assertIsInstance(result, RestoreExecutionResult)

    def test_pipeline_prepare_then_execute(self):
        class MockPipeline(RestoreExecutionPipeline):
            def __init__(self):
                self.prepared = False
            def prepare(self, request):
                self.prepared = True
            def execute(self, request):
                return RestoreExecutionResult(
                    restore_id=request.restore_id,
                    status=RestoreExecutionStatus.COMPLETED,
                    success=self.prepared, message="ok" if self.prepared else "not prepared",
                )
        pipeline = MockPipeline()
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        pipeline.prepare(req)
        result = pipeline.execute(req)
        self.assertTrue(result.success)

    def test_error_messages_safe(self):
        try:
            raise RestoreExecutionError("test")
        except RestoreExecutionError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_conflict_error_message(self):
        exc = RestoreExecutionConflictError("test-restore")
        self.assertIn("test-restore", str(exc))

    def test_unavailable_error_message(self):
        exc = RestoreExecutionUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_result_empty_message_accepted(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="",
        )
        self.assertEqual(result.message, "")

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            RestoreExecutionRequest(
                restore_id="   ", operation_id="op-001",
                job_id="j-001", execution_id="exec-001",
                adapter_id="linux-001", backup_id="b-001",
            )

    def test_request_whitespace_backup_id_rejected(self):
        with self.assertRaises(InvalidRestoreExecutionRequestError):
            RestoreExecutionRequest(
                restore_id="r-001", operation_id="op-001",
                job_id="j-001", execution_id="exec-001",
                adapter_id="linux-001", backup_id="   ",
            )

    def test_result_all_statuses(self):
        for status in RestoreExecutionStatus:
            result = RestoreExecutionResult(
                restore_id="r-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_pipeline_returns_result(self):
        class MockPipeline(RestoreExecutionPipeline):
            def prepare(self, request):
                pass
            def execute(self, request):
                return RestoreExecutionResult(
                    restore_id=request.restore_id,
                    status=RestoreExecutionStatus.COMPLETED,
                    success=True, message="ok",
                )
        pipeline = MockPipeline()
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        result = pipeline.execute(req)
        self.assertIsInstance(result, RestoreExecutionResult)

    def test_request_no_command(self):
        req = RestoreExecutionRequest(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", execution_id="exec-001",
            adapter_id="linux-001", backup_id="b-001",
        )
        self.assertFalse(hasattr(req, "command"))

    def test_result_no_stderr(self):
        result = RestoreExecutionResult(
            restore_id="r-001", status=RestoreExecutionStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))


if __name__ == "__main__":
    unittest.main()
