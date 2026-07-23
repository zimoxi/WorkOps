"""
WorkOps Backup Workflow v1 Tests
Sprint041: Backup Workflow Foundation v1

覆盖：
- BackupType enum
- BackupStatus validation
- BackupRequest model
- BackupResult model
- BackupWorkflow model
- BackupWorkflowExecutor contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.backup.workflow_model import BackupType, BackupStatus, BackupWorkflow
from backup_manager.backup.workflow_request import BackupRequest
from backup_manager.backup.workflow_result import BackupResult
from backup_manager.backup.workflow_executor import BackupWorkflowExecutor
from backup_manager.backup.workflow_errors import (
    BackupWorkflowError,
    InvalidBackupRequestError,
    BackupConflictError,
    BackupNotFoundError,
)


# ============================================================================
# BackupType
# ============================================================================

class TestBackupType(unittest.TestCase):
    """备份类型测试"""

    def test_full(self):
        self.assertEqual(BackupType.FULL.value, "full")

    def test_incremental(self):
        self.assertEqual(BackupType.INCREMENTAL.value, "incremental")

    def test_two_types(self):
        self.assertEqual(len(BackupType), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            BackupType("nonexistent")


# ============================================================================
# BackupStatus
# ============================================================================

class TestBackupStatus(unittest.TestCase):
    """备份状态测试"""

    def test_created(self):
        self.assertEqual(BackupStatus.CREATED, "created")

    def test_queued(self):
        self.assertEqual(BackupStatus.QUEUED, "queued")

    def test_running(self):
        self.assertEqual(BackupStatus.RUNNING, "running")

    def test_success(self):
        self.assertEqual(BackupStatus.SUCCESS, "success")

    def test_failed(self):
        self.assertEqual(BackupStatus.FAILED, "failed")

    def test_cancelled(self):
        self.assertEqual(BackupStatus.CANCELLED, "cancelled")

    def test_six_statuses(self):
        self.assertEqual(len(BackupStatus._VALID), 6)

    def test_validate_valid(self):
        for status in BackupStatus._VALID:
            self.assertEqual(BackupStatus.validate(status), status)

    def test_validate_invalid(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupStatus.validate("nonexistent")


# ============================================================================
# BackupRequest
# ============================================================================

class TestBackupRequest(unittest.TestCase):
    """备份请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "backup_id": "b-001",
            "device_id": "dev-001",
            "backup_type": BackupType.FULL,
        }
        defaults.update(kwargs)
        return BackupRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.backup_id, "b-001")
        self.assertEqual(req.device_id, "dev-001")
        self.assertEqual(req.backup_type, BackupType.FULL)

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.backup_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            self._make_request(backup_id="")

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            self._make_request(device_id="")

    def test_invalid_backup_type_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            self._make_request(backup_type="full")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_incremental_type(self):
        req = self._make_request(backup_type=BackupType.INCREMENTAL)
        self.assertEqual(req.backup_type, BackupType.INCREMENTAL)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "command", "destination_path", "storage_path"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# BackupResult
# ============================================================================

class TestBackupResult(unittest.TestCase):
    """备份结果测试"""

    def test_valid_result(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="done",
        )
        self.assertEqual(result.backup_id, "b-001")
        self.assertTrue(result.success)

    def test_frozen(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.backup_id = "other"

    def test_slots(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupResult(
                backup_id="", status=BackupStatus.SUCCESS,
                success=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupResult(
                backup_id="b-001", status="nonexistent",
                success=True, message="ok",
            )

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupResult(
                backup_id="b-001", status=BackupStatus.SUCCESS,
                success=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupResult(
                backup_id="b-001", status=BackupStatus.SUCCESS,
                success=True, message=123,
            )

    def test_timezone_aware(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="ok",
        )
        self.assertIsNotNone(result.finished_at.tzinfo)

    def test_no_forbidden_fields(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# BackupWorkflow
# ============================================================================

class TestBackupWorkflow(unittest.TestCase):
    """备份工作流测试"""

    def test_valid_workflow(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        self.assertEqual(wf.backup_id, "b-001")
        self.assertEqual(wf.operation_id, "op-001")
        self.assertEqual(wf.job_id, "j-001")

    def test_frozen(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        with self.assertRaises(AttributeError):
            wf.backup_id = "other"

    def test_slots(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        with self.assertRaises(AttributeError):
            wf.__dict__

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupWorkflow(backup_id="", operation_id="op-001", job_id="j-001")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupWorkflow(backup_id="b-001", operation_id="", job_id="j-001")

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidBackupRequestError):
            BackupWorkflow(backup_id="b-001", operation_id="op-001", job_id="")

    def test_timezone_aware(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        self.assertIsNotNone(wf.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(wf, attr))


# ============================================================================
# BackupWorkflowExecutor Contract
# ============================================================================

class TestBackupWorkflowExecutorContract(unittest.TestCase):
    """执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(BackupWorkflowExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(BackupWorkflowExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            BackupWorkflowExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(BackupWorkflowExecutor):
            def execute(self, request):
                return BackupResult(
                    backup_id=request.backup_id,
                    status=BackupStatus.SUCCESS,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = BackupRequest(
            backup_id="b-001", device_id="dev-001",
            backup_type=BackupType.FULL,
        )
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadExecutor(BackupWorkflowExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# Error Model
# ============================================================================

class TestBackupWorkflowErrors(unittest.TestCase):
    """错误模型测试"""

    def test_workflow_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise BackupWorkflowError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise InvalidBackupRequestError("test")

    def test_conflict_error(self):
        exc = BackupConflictError("b-001")
        self.assertIn("b-001", str(exc))

    def test_not_found_error(self):
        exc = BackupNotFoundError("b-001")
        self.assertIn("b-001", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (BackupWorkflowError, ("test",)),
            (InvalidBackupRequestError, ("test",)),
            (BackupConflictError, ("b-001",)),
            (BackupNotFoundError, ("b-001",)),
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
        req = BackupRequest(
            backup_id="b-001", device_id="dev-001",
            backup_type=BackupType.FULL,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="ok",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_workflow_no_credentials(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(wf, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["workflow_model.py", "workflow_request.py", "workflow_result.py",
                         "workflow_executor.py", "workflow_errors.py"]:
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
        for filename in ["workflow_model.py", "workflow_request.py", "workflow_result.py",
                         "workflow_executor.py", "workflow_errors.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_request_repr_no_secrets(self):
        req = BackupRequest(
            backup_id="b-001", device_id="dev-001",
            backup_type=BackupType.FULL,
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = BackupResult(
            backup_id="b-001", status=BackupStatus.SUCCESS,
            success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_workflow_repr_no_secrets(self):
        wf = BackupWorkflow(
            backup_id="b-001", operation_id="op-001", job_id="j-001",
        )
        r = repr(wf)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidBackupRequestError, BackupWorkflowError))
        self.assertTrue(issubclass(BackupConflictError, BackupWorkflowError))
        self.assertTrue(issubclass(BackupNotFoundError, BackupWorkflowError))

    def test_all_backup_statuses(self):
        for status in BackupStatus._VALID:
            result = BackupResult(
                backup_id="b-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)


if __name__ == "__main__":
    unittest.main()
