"""
WorkOps Restore Workflow Tests
Sprint036: Restore Workflow Foundation

覆盖：
- RestoreJob validation
- RestoreExecution state handling
- RestorePolicy validation
- RestoreExecutionState enum
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.restore.models import RestoreJob
from backup_manager.restore.execution import RestoreExecution
from backup_manager.restore.policy import RestorePolicy, OverwriteMode
from backup_manager.restore.state import RestoreExecutionState
from backup_manager.restore.errors import (
    RestoreWorkflowError,
    InvalidRestoreJobError,
    InvalidRestorePolicyError,
)


# ============================================================================
# RestoreJob
# ============================================================================

class TestRestoreJob(unittest.TestCase):
    """恢复任务测试"""

    def _make_job(self, **kwargs):
        defaults = {
            "restore_id": "r1",
            "source_backup_id": "b1",
            "target_device_id": "d1",
        }
        defaults.update(kwargs)
        return RestoreJob(**defaults)

    def test_valid_job(self):
        job = self._make_job()
        self.assertEqual(job.restore_id, "r1")
        self.assertEqual(job.source_backup_id, "b1")
        self.assertEqual(job.target_device_id, "d1")
        self.assertEqual(job.status, RestoreExecutionState.PENDING)

    def test_frozen(self):
        job = self._make_job()
        with self.assertRaises(AttributeError):
            job.restore_id = "other"

    def test_slots(self):
        job = self._make_job()
        with self.assertRaises(AttributeError):
            job.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidRestoreJobError):
            self._make_job(restore_id="")

    def test_empty_source_backup_id_rejected(self):
        with self.assertRaises(InvalidRestoreJobError):
            self._make_job(source_backup_id="")

    def test_empty_target_device_id_rejected(self):
        with self.assertRaises(InvalidRestoreJobError):
            self._make_job(target_device_id="")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidRestoreJobError):
            self._make_job(status="pending")

    def test_custom_status(self):
        job = self._make_job(status=RestoreExecutionState.SUCCESS)
        self.assertEqual(job.status, RestoreExecutionState.SUCCESS)

    def test_timezone_aware(self):
        job = self._make_job()
        self.assertIsNotNone(job.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        job = self._make_job()
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(job, attr))

    def test_repr_no_secrets(self):
        job = self._make_job()
        r = repr(job)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RestoreExecution
# ============================================================================

class TestRestoreExecution(unittest.TestCase):
    """恢复执行测试"""

    def test_valid_execution(self):
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        self.assertEqual(execution.execution_id, "e1")
        self.assertEqual(execution.restore_id, "r1")
        self.assertEqual(execution.state, RestoreExecutionState.PENDING)
        self.assertIsNone(execution.started_at)
        self.assertIsNone(execution.finished_at)
        self.assertEqual(execution.message, "")

    def test_frozen(self):
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        with self.assertRaises(AttributeError):
            execution.execution_id = "other"

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(RestoreWorkflowError):
            RestoreExecution(execution_id="", restore_id="r1")

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(RestoreWorkflowError):
            RestoreExecution(execution_id="e1", restore_id="")

    def test_invalid_state_rejected(self):
        with self.assertRaises(RestoreWorkflowError):
            RestoreExecution(execution_id="e1", restore_id="r1", state="pending")

    def test_started_at_must_be_datetime(self):
        with self.assertRaises(RestoreWorkflowError):
            RestoreExecution(execution_id="e1", restore_id="r1", started_at="not_dt")

    def test_finished_at_must_be_datetime(self):
        with self.assertRaises(RestoreWorkflowError):
            RestoreExecution(execution_id="e1", restore_id="r1", finished_at="not_dt")

    def test_message_must_be_str(self):
        with self.assertRaises(RestoreWorkflowError):
            RestoreExecution(execution_id="e1", restore_id="r1", message=123)

    def test_with_timestamps(self):
        now = datetime.now(timezone.utc)
        execution = RestoreExecution(
            execution_id="e1", restore_id="r1",
            state=RestoreExecutionState.SUCCESS,
            started_at=now, finished_at=now, message="done",
        )
        self.assertEqual(execution.state, RestoreExecutionState.SUCCESS)
        self.assertIsNotNone(execution.started_at)
        self.assertIsNotNone(execution.finished_at)

    def test_no_forbidden_fields(self):
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(execution, attr))


# ============================================================================
# RestorePolicy
# ============================================================================

class TestRestorePolicy(unittest.TestCase):
    """恢复策略测试"""

    def test_valid_policy(self):
        policy = RestorePolicy(policy_id="p1")
        self.assertEqual(policy.policy_id, "p1")
        self.assertEqual(policy.overwrite_mode, OverwriteMode.NEVER)
        self.assertTrue(policy.verification_required)

    def test_frozen(self):
        policy = RestorePolicy(policy_id="p1")
        with self.assertRaises(AttributeError):
            policy.policy_id = "other"

    def test_empty_policy_id_rejected(self):
        with self.assertRaises(InvalidRestorePolicyError):
            RestorePolicy(policy_id="")

    def test_invalid_overwrite_mode_rejected(self):
        with self.assertRaises(InvalidRestorePolicyError):
            RestorePolicy(policy_id="p1", overwrite_mode="never")

    def test_verification_must_be_bool(self):
        with self.assertRaises(InvalidRestorePolicyError):
            RestorePolicy(policy_id="p1", verification_required=1)

    def test_custom_overwrite_mode(self):
        policy = RestorePolicy(policy_id="p1", overwrite_mode=OverwriteMode.ALWAYS)
        self.assertEqual(policy.overwrite_mode, OverwriteMode.ALWAYS)

    def test_verification_false(self):
        policy = RestorePolicy(policy_id="p1", verification_required=False)
        self.assertFalse(policy.verification_required)

    def test_no_forbidden_fields(self):
        policy = RestorePolicy(policy_id="p1")
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(policy, attr))


# ============================================================================
# OverwriteMode
# ============================================================================

class TestOverwriteMode(unittest.TestCase):
    """覆盖模式测试"""

    def test_never(self):
        self.assertEqual(OverwriteMode.NEVER.value, "never")

    def test_always(self):
        self.assertEqual(OverwriteMode.ALWAYS.value, "always")

    def test_newer(self):
        self.assertEqual(OverwriteMode.NEWER.value, "newer")

    def test_three_modes(self):
        self.assertEqual(len(OverwriteMode), 3)


# ============================================================================
# RestoreExecutionState
# ============================================================================

class TestRestoreExecutionState(unittest.TestCase):
    """恢复执行状态测试"""

    def test_pending(self):
        self.assertEqual(RestoreExecutionState.PENDING.value, "pending")

    def test_running(self):
        self.assertEqual(RestoreExecutionState.RUNNING.value, "running")

    def test_success(self):
        self.assertEqual(RestoreExecutionState.SUCCESS.value, "success")

    def test_failed(self):
        self.assertEqual(RestoreExecutionState.FAILED.value, "failed")

    def test_cancelled(self):
        self.assertEqual(RestoreExecutionState.CANCELLED.value, "cancelled")

    def test_five_states(self):
        self.assertEqual(len(RestoreExecutionState), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RestoreExecutionState("nonexistent")


# ============================================================================
# Error Model
# ============================================================================

class TestRestoreErrors(unittest.TestCase):
    """错误模型测试"""

    def test_workflow_error(self):
        with self.assertRaises(RestoreWorkflowError):
            raise RestoreWorkflowError("test")

    def test_invalid_job_error(self):
        with self.assertRaises(RestoreWorkflowError):
            raise InvalidRestoreJobError("test")

    def test_invalid_policy_error(self):
        with self.assertRaises(RestoreWorkflowError):
            raise InvalidRestorePolicyError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (RestoreWorkflowError, ("test",)),
            (InvalidRestoreJobError, ("test",)),
            (InvalidRestorePolicyError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "command"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_job_no_credentials(self):
        job = RestoreJob(
            restore_id="r1", source_backup_id="b1", target_device_id="d1",
        )
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(job, attr))

    def test_execution_no_credentials(self):
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(execution, attr))

    def test_policy_no_credentials(self):
        policy = RestorePolicy(policy_id="p1")
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(policy, attr))

    def test_no_subprocess(self):
        import ast
        import os
        restore_dir = os.path.join("backup_manager", "restore")
        for filename in os.listdir(restore_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(restore_dir, filename)
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
        restore_dir = os.path.join("backup_manager", "restore")
        for filename in os.listdir(restore_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(restore_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_repr_no_secrets(self):
        job = RestoreJob(
            restore_id="r1", source_backup_id="b1", target_device_id="d1",
        )
        r = repr(job)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# Extended Tests
# ============================================================================

class TestRestoreJobExtended(unittest.TestCase):
    """恢复任务扩展测试"""

    def test_all_states(self):
        for state in RestoreExecutionState:
            job = RestoreJob(
                restore_id="r1", source_backup_id="b1",
                target_device_id="d1", status=state,
            )
            self.assertEqual(job.status, state)

    def test_execution_all_states(self):
        for state in RestoreExecutionState:
            execution = RestoreExecution(
                execution_id="e1", restore_id="r1", state=state,
            )
            self.assertEqual(execution.state, state)

    def test_policy_all_overwrite_modes(self):
        for mode in OverwriteMode:
            policy = RestorePolicy(policy_id="p1", overwrite_mode=mode)
            self.assertEqual(policy.overwrite_mode, mode)

    def test_job_repr_no_secrets(self):
        job = RestoreJob(
            restore_id="r1", source_backup_id="b1", target_device_id="d1",
        )
        r = repr(job)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_execution_repr_no_secrets(self):
        execution = RestoreExecution(execution_id="e1", restore_id="r1")
        r = repr(execution)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_policy_repr_no_secrets(self):
        policy = RestorePolicy(policy_id="p1")
        r = repr(policy)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_execution_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidRestoreJobError, RestoreWorkflowError))
        self.assertTrue(issubclass(InvalidRestorePolicyError, RestoreWorkflowError))

    def test_job_error_messages_safe(self):
        try:
            raise InvalidRestoreJobError("test")
        except InvalidRestoreJobError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_policy_error_messages_safe(self):
        try:
            raise InvalidRestorePolicyError("test")
        except InvalidRestorePolicyError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_overwrite_mode_invalid(self):
        with self.assertRaises(ValueError):
            OverwriteMode("invalid")


if __name__ == "__main__":
    unittest.main()
