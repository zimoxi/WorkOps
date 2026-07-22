"""
WorkOps Backup Execution Engine Tests
Sprint030: Backup Execution Engine

覆盖：
- BackupExecution model
- State transitions
- BackupExecutionService lifecycle
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.backup.execution import BackupExecution
from backup_manager.backup.state import BackupExecutionState
from backup_manager.backup.execution_state import validate_transition
from backup_manager.backup.execution_service import BackupExecutionService
from backup_manager.backup.errors import (
    BackupExecutionError,
    InvalidStateTransitionError,
    BackupWorkflowError,
)


# ============================================================================
# BackupExecution Model
# ============================================================================

class TestBackupExecutionModel(unittest.TestCase):
    """执行模型测试"""

    def test_valid_execution(self):
        execution = BackupExecution(
            execution_id="exec-001",
            job_id="job-001",
        )
        self.assertEqual(execution.execution_id, "exec-001")
        self.assertEqual(execution.job_id, "job-001")
        self.assertEqual(execution.state, BackupExecutionState.PENDING)
        self.assertIsNone(execution.started_at)
        self.assertIsNone(execution.finished_at)
        self.assertEqual(execution.message, "")

    def test_frozen(self):
        execution = BackupExecution(execution_id="e1", job_id="j1")
        with self.assertRaises(AttributeError):
            execution.execution_id = "other"

    def test_slots(self):
        execution = BackupExecution(execution_id="e1", job_id="j1")
        with self.assertRaises(AttributeError):
            execution.__dict__

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(BackupExecutionError):
            BackupExecution(execution_id="", job_id="j1")

    def test_empty_job_id_rejected(self):
        with self.assertRaises(BackupExecutionError):
            BackupExecution(execution_id="e1", job_id="")

    def test_invalid_state_rejected(self):
        with self.assertRaises(BackupExecutionError):
            BackupExecution(execution_id="e1", job_id="j1", state="pending")

    def test_started_at_must_be_datetime(self):
        with self.assertRaises(BackupExecutionError):
            BackupExecution(execution_id="e1", job_id="j1", started_at="not_a_dt")

    def test_finished_at_must_be_datetime(self):
        with self.assertRaises(BackupExecutionError):
            BackupExecution(execution_id="e1", job_id="j1", finished_at="not_a_dt")

    def test_message_must_be_str(self):
        with self.assertRaises(BackupExecutionError):
            BackupExecution(execution_id="e1", job_id="j1", message=123)

    def test_with_timestamps(self):
        now = datetime.now(timezone.utc)
        execution = BackupExecution(
            execution_id="e1",
            job_id="j1",
            state=BackupExecutionState.SUCCESS,
            started_at=now,
            finished_at=now,
            message="done",
        )
        self.assertEqual(execution.state, BackupExecutionState.SUCCESS)
        self.assertIsNotNone(execution.started_at)
        self.assertIsNotNone(execution.finished_at)

    def test_no_forbidden_fields(self):
        execution = BackupExecution(execution_id="e1", job_id="j1")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(execution, attr))

    def test_repr_no_secrets(self):
        execution = BackupExecution(execution_id="e1", job_id="j1")
        r = repr(execution)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# State Transitions
# ============================================================================

class TestStateTransitions(unittest.TestCase):
    """状态转换测试"""

    def test_pending_to_running(self):
        validate_transition(BackupExecutionState.PENDING, BackupExecutionState.RUNNING)

    def test_running_to_success(self):
        validate_transition(BackupExecutionState.RUNNING, BackupExecutionState.SUCCESS)

    def test_running_to_failed(self):
        validate_transition(BackupExecutionState.RUNNING, BackupExecutionState.FAILED)

    def test_running_to_cancelled(self):
        validate_transition(BackupExecutionState.RUNNING, BackupExecutionState.CANCELLED)

    def test_success_to_running_rejected(self):
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(BackupExecutionState.SUCCESS, BackupExecutionState.RUNNING)

    def test_failed_to_running_rejected(self):
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(BackupExecutionState.FAILED, BackupExecutionState.RUNNING)

    def test_cancelled_to_running_rejected(self):
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(BackupExecutionState.CANCELLED, BackupExecutionState.RUNNING)

    def test_pending_to_success_rejected(self):
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(BackupExecutionState.PENDING, BackupExecutionState.SUCCESS)

    def test_pending_to_failed_rejected(self):
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(BackupExecutionState.PENDING, BackupExecutionState.FAILED)

    def test_success_to_failed_rejected(self):
        with self.assertRaises(InvalidStateTransitionError):
            validate_transition(BackupExecutionState.SUCCESS, BackupExecutionState.FAILED)

    def test_error_message_format(self):
        try:
            validate_transition(BackupExecutionState.SUCCESS, BackupExecutionState.RUNNING)
        except InvalidStateTransitionError as e:
            self.assertIn("success", str(e))
            self.assertIn("running", str(e))

    def test_error_no_secrets(self):
        try:
            validate_transition(BackupExecutionState.SUCCESS, BackupExecutionState.RUNNING)
        except InvalidStateTransitionError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# BackupExecutionService
# ============================================================================

class TestBackupExecutionService(unittest.TestCase):
    """执行服务测试"""

    def setUp(self):
        self.service = BackupExecutionService()

    def test_create_execution(self):
        execution = self.service.create_execution("job-001")
        self.assertEqual(execution.state, BackupExecutionState.PENDING)
        self.assertEqual(execution.job_id, "job-001")
        self.assertIsNotNone(execution.execution_id)

    def test_start_execution(self):
        execution = self.service.create_execution("job-001")
        started = self.service.start_execution(execution.execution_id)
        self.assertEqual(started.state, BackupExecutionState.RUNNING)
        self.assertIsNotNone(started.started_at)

    def test_complete_execution(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        completed = self.service.complete_execution(execution.execution_id, "done")
        self.assertEqual(completed.state, BackupExecutionState.SUCCESS)
        self.assertIsNotNone(completed.finished_at)
        self.assertEqual(completed.message, "done")

    def test_fail_execution(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        failed = self.service.fail_execution(execution.execution_id, "error")
        self.assertEqual(failed.state, BackupExecutionState.FAILED)
        self.assertEqual(failed.message, "error")

    def test_cancel_execution(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        cancelled = self.service.cancel_execution(execution.execution_id, "user cancelled")
        self.assertEqual(cancelled.state, BackupExecutionState.CANCELLED)

    def test_full_lifecycle(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        result = self.service.complete_execution(execution.execution_id)
        self.assertEqual(result.state, BackupExecutionState.SUCCESS)

    def test_fail_lifecycle(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        result = self.service.fail_execution(execution.execution_id)
        self.assertEqual(result.state, BackupExecutionState.FAILED)

    def test_cancel_lifecycle(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        result = self.service.cancel_execution(execution.execution_id)
        self.assertEqual(result.state, BackupExecutionState.CANCELLED)

    def test_start_nonexistent_rejected(self):
        with self.assertRaises(BackupExecutionError):
            self.service.start_execution("nonexistent")

    def test_complete_nonexistent_rejected(self):
        with self.assertRaises(BackupExecutionError):
            self.service.complete_execution("nonexistent")

    def test_fail_nonexistent_rejected(self):
        with self.assertRaises(BackupExecutionError):
            self.service.fail_execution("nonexistent")

    def test_cancel_nonexistent_rejected(self):
        with self.assertRaises(BackupExecutionError):
            self.service.cancel_execution("nonexistent")

    def test_invalid_transition_from_pending_to_success(self):
        execution = self.service.create_execution("job-001")
        with self.assertRaises(InvalidStateTransitionError):
            self.service.complete_execution(execution.execution_id)

    def test_invalid_transition_from_success_to_running(self):
        execution = self.service.create_execution("job-001")
        self.service.start_execution(execution.execution_id)
        self.service.complete_execution(execution.execution_id)
        with self.assertRaises(InvalidStateTransitionError):
            self.service.start_execution(execution.execution_id)

    def test_get_execution(self):
        execution = self.service.create_execution("job-001")
        got = self.service.get_execution(execution.execution_id)
        self.assertEqual(got.execution_id, execution.execution_id)

    def test_list_executions(self):
        self.service.create_execution("job-001")
        self.service.create_execution("job-002")
        self.assertEqual(len(self.service.list_executions()), 2)

    def test_no_real_execution(self):
        """确认服务没有真实的执行方法"""
        service = BackupExecutionService()
        for method in ["execute_backup", "run_backup", "copy_files", "rsync"]:
            self.assertFalse(hasattr(service, method))


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_execution_no_credentials(self):
        execution = BackupExecution(execution_id="e1", job_id="j1")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(execution, attr))

    def test_service_no_credentials(self):
        service = BackupExecutionService()
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(service, attr))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (BackupExecutionError, ("test",)),
            (InvalidStateTransitionError, ("pending", "running")),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())

    def test_no_subprocess(self):
        import ast
        import os
        backup_dir = os.path.join("backup_manager", "backup")
        for filename in ["execution.py", "execution_state.py", "execution_service.py"]:
            filepath = os.path.join(backup_dir, filename)
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
        backup_dir = os.path.join("backup_manager", "backup")
        for filename in ["execution.py", "execution_state.py", "execution_service.py"]:
            filepath = os.path.join(backup_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_execution_repr_no_secrets(self):
        execution = BackupExecution(execution_id="e1", job_id="j1")
        r = repr(execution)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_service_list_empty(self):
        service = BackupExecutionService()
        self.assertEqual(service.list_executions(), [])


# ============================================================================
# Additional Execution Service Tests
# ============================================================================

class TestBackupExecutionServiceExtended(unittest.TestCase):
    """执行服务扩展测试"""

    def setUp(self):
        self.service = BackupExecutionService()

    def test_create_multiple_executions(self):
        e1 = self.service.create_execution("job-001")
        e2 = self.service.create_execution("job-002")
        self.assertNotEqual(e1.execution_id, e2.execution_id)
        self.assertEqual(len(self.service.list_executions()), 2)

    def test_state_transitions_exhaustive(self):
        """确认所有终态不能再转换"""
        for terminal_state in [
            BackupExecutionState.SUCCESS,
            BackupExecutionState.FAILED,
            BackupExecutionState.CANCELLED,
        ]:
            for target in BackupExecutionState:
                if target == terminal_state:
                    continue
                with self.assertRaises(InvalidStateTransitionError):
                    validate_transition(terminal_state, target)


if __name__ == "__main__":
    unittest.main()
