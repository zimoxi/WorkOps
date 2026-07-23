"""
WorkOps Restore Workflow v1 Tests
Sprint042: Restore Workflow Foundation v1

覆盖：
- RestoreType enum
- RestoreStatus validation
- RestoreRequest model
- RestoreResult model
- RestoreWorkflow model
- RestoreWorkflowExecutor contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.restore_workflow.model import RestoreType, RestoreStatus, RestoreWorkflow
from backup_manager.restore_workflow.request import RestoreRequest
from backup_manager.restore_workflow.result import RestoreResult
from backup_manager.restore_workflow.executor import RestoreWorkflowExecutor
from backup_manager.restore_workflow.errors import (
    RestoreWorkflowV1Error,
    InvalidRestoreRequestError,
    RestoreConflictError,
    RestoreNotFoundError,
)


# ============================================================================
# RestoreType
# ============================================================================

class TestRestoreType(unittest.TestCase):
    """恢复类型测试"""

    def test_full(self):
        self.assertEqual(RestoreType.FULL.value, "full")

    def test_selective(self):
        self.assertEqual(RestoreType.SELECTIVE.value, "selective")

    def test_two_types(self):
        self.assertEqual(len(RestoreType), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RestoreType("nonexistent")


# ============================================================================
# RestoreStatus
# ============================================================================

class TestRestoreStatus(unittest.TestCase):
    """恢复状态测试"""

    def test_created(self):
        self.assertEqual(RestoreStatus.CREATED, "created")

    def test_queued(self):
        self.assertEqual(RestoreStatus.QUEUED, "queued")

    def test_running(self):
        self.assertEqual(RestoreStatus.RUNNING, "running")

    def test_success(self):
        self.assertEqual(RestoreStatus.SUCCESS, "success")

    def test_failed(self):
        self.assertEqual(RestoreStatus.FAILED, "failed")

    def test_cancelled(self):
        self.assertEqual(RestoreStatus.CANCELLED, "cancelled")

    def test_six_statuses(self):
        self.assertEqual(len(RestoreStatus._VALID), 6)

    def test_validate_valid(self):
        for status in RestoreStatus._VALID:
            self.assertEqual(RestoreStatus.validate(status), status)

    def test_validate_invalid(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreStatus.validate("nonexistent")


# ============================================================================
# RestoreRequest
# ============================================================================

class TestRestoreRequest(unittest.TestCase):
    """恢复请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "restore_id": "r-001",
            "device_id": "dev-001",
            "backup_id": "b-001",
            "restore_type": RestoreType.FULL,
        }
        defaults.update(kwargs)
        return RestoreRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.restore_id, "r-001")
        self.assertEqual(req.device_id, "dev-001")
        self.assertEqual(req.backup_id, "b-001")
        self.assertEqual(req.restore_type, RestoreType.FULL)

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.restore_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            self._make_request(restore_id="")

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            self._make_request(device_id="")

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            self._make_request(backup_id="")

    def test_invalid_restore_type_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            self._make_request(restore_type="full")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_selective_type(self):
        req = self._make_request(restore_type=RestoreType.SELECTIVE)
        self.assertEqual(req.restore_type, RestoreType.SELECTIVE)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "command", "source_path", "destination_path"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RestoreResult
# ============================================================================

class TestRestoreResult(unittest.TestCase):
    """恢复结果测试"""

    def test_valid_result(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="done",
        )
        self.assertEqual(result.restore_id, "r-001")
        self.assertTrue(result.success)

    def test_frozen(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.restore_id = "other"

    def test_slots(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreResult(
                restore_id="", status=RestoreStatus.SUCCESS,
                success=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreResult(
                restore_id="r-001", status="nonexistent",
                success=True, message="ok",
            )

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreResult(
                restore_id="r-001", status=RestoreStatus.SUCCESS,
                success=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreResult(
                restore_id="r-001", status=RestoreStatus.SUCCESS,
                success=True, message=123,
            )

    def test_timezone_aware(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="ok",
        )
        self.assertIsNotNone(result.finished_at.tzinfo)

    def test_no_forbidden_fields(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# RestoreWorkflow
# ============================================================================

class TestRestoreWorkflow(unittest.TestCase):
    """恢复工作流测试"""

    def test_valid_workflow(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        self.assertEqual(wf.restore_id, "r-001")
        self.assertEqual(wf.operation_id, "op-001")
        self.assertEqual(wf.job_id, "j-001")
        self.assertEqual(wf.backup_id, "b-001")

    def test_frozen(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        with self.assertRaises(AttributeError):
            wf.restore_id = "other"

    def test_slots(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        with self.assertRaises(AttributeError):
            wf.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreWorkflow(restore_id="", operation_id="op-001", job_id="j-001", backup_id="b-001")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreWorkflow(restore_id="r-001", operation_id="", job_id="j-001", backup_id="b-001")

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreWorkflow(restore_id="r-001", operation_id="op-001", job_id="", backup_id="b-001")

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidRestoreRequestError):
            RestoreWorkflow(restore_id="r-001", operation_id="op-001", job_id="j-001", backup_id="")

    def test_timezone_aware(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        self.assertIsNotNone(wf.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(wf, attr))


# ============================================================================
# RestoreWorkflowExecutor Contract
# ============================================================================

class TestRestoreWorkflowExecutorContract(unittest.TestCase):
    """执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreWorkflowExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(RestoreWorkflowExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreWorkflowExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(RestoreWorkflowExecutor):
            def execute(self, request):
                return RestoreResult(
                    restore_id=request.restore_id,
                    status=RestoreStatus.SUCCESS,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = RestoreRequest(
            restore_id="r-001", device_id="dev-001",
            backup_id="b-001", restore_type=RestoreType.FULL,
        )
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadExecutor(RestoreWorkflowExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# Error Model
# ============================================================================

class TestRestoreWorkflowErrors(unittest.TestCase):
    """错误模型测试"""

    def test_workflow_error(self):
        with self.assertRaises(RestoreWorkflowV1Error):
            raise RestoreWorkflowV1Error("test")

    def test_invalid_request_error(self):
        with self.assertRaises(RestoreWorkflowV1Error):
            raise InvalidRestoreRequestError("test")

    def test_conflict_error(self):
        exc = RestoreConflictError("r-001")
        self.assertIn("r-001", str(exc))

    def test_not_found_error(self):
        exc = RestoreNotFoundError("r-001")
        self.assertIn("r-001", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (RestoreWorkflowV1Error, ("test",)),
            (InvalidRestoreRequestError, ("test",)),
            (RestoreConflictError, ("r-001",)),
            (RestoreNotFoundError, ("r-001",)),
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
        req = RestoreRequest(
            restore_id="r-001", device_id="dev-001",
            backup_id="b-001", restore_type=RestoreType.FULL,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="ok",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_workflow_no_credentials(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(wf, attr))

    def test_no_subprocess(self):
        import ast
        import os
        rw_dir = os.path.join("backup_manager", "restore_workflow")
        for filename in os.listdir(rw_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(rw_dir, filename)
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
        rw_dir = os.path.join("backup_manager", "restore_workflow")
        for filename in os.listdir(rw_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(rw_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")


# ============================================================================
# Extended Tests
# ============================================================================

class TestRestoreWorkflowExtended(unittest.TestCase):
    """扩展测试"""

    def test_all_restore_statuses(self):
        for status in RestoreStatus._VALID:
            result = RestoreResult(
                restore_id="r-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidRestoreRequestError, RestoreWorkflowV1Error))
        self.assertTrue(issubclass(RestoreConflictError, RestoreWorkflowV1Error))
        self.assertTrue(issubclass(RestoreNotFoundError, RestoreWorkflowV1Error))

    def test_request_repr_no_secrets(self):
        req = RestoreRequest(
            restore_id="r-001", device_id="dev-001",
            backup_id="b-001", restore_type=RestoreType.FULL,
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = RestoreResult(
            restore_id="r-001", status=RestoreStatus.SUCCESS,
            success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_workflow_repr_no_secrets(self):
        wf = RestoreWorkflow(
            restore_id="r-001", operation_id="op-001",
            job_id="j-001", backup_id="b-001",
        )
        r = repr(wf)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


if __name__ == "__main__":
    unittest.main()
