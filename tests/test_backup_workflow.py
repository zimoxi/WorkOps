"""
WorkOps Backup Workflow Tests
Sprint029: Backup Workflow Foundation

覆盖：
- BackupJob validation
- BackupSchedule validation
- BackupPolicy validation
- BackupExecutionState enum
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.backup.models import BackupJob
from backup_manager.backup.schedule import BackupSchedule
from backup_manager.backup.policy import BackupPolicy
from backup_manager.backup.state import BackupExecutionState
from backup_manager.backup.errors import (
    BackupWorkflowError,
    InvalidBackupJobError,
    InvalidPolicyError,
)


# ============================================================================
# BackupJob
# ============================================================================

class TestBackupJob(unittest.TestCase):
    """备份任务测试"""

    def _make_job(self, **kwargs):
        defaults = {
            "job_id": "job-001",
            "name": "Daily Backup",
            "source_device_id": "dev-001",
            "target_device_id": "dev-002",
            "schedule_id": "sched-001",
            "policy_id": "pol-001",
        }
        defaults.update(kwargs)
        return BackupJob(**defaults)

    def test_valid_job(self):
        job = self._make_job()
        self.assertEqual(job.job_id, "job-001")
        self.assertEqual(job.name, "Daily Backup")
        self.assertTrue(job.enabled)

    def test_frozen(self):
        job = self._make_job()
        with self.assertRaises(AttributeError):
            job.job_id = "other"

    def test_slots(self):
        job = self._make_job()
        with self.assertRaises(AttributeError):
            job.__dict__

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(job_id="")

    def test_empty_name_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(name="")

    def test_empty_source_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(source_device_id="")

    def test_empty_target_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(target_device_id="")

    def test_empty_schedule_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(schedule_id="")

    def test_empty_policy_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(policy_id="")

    def test_enabled_must_be_bool(self):
        with self.assertRaises(InvalidBackupJobError):
            self._make_job(enabled=1)

    def test_enabled_false(self):
        job = self._make_job(enabled=False)
        self.assertFalse(job.enabled)

    def test_timezone_aware(self):
        job = self._make_job()
        self.assertIsNotNone(job.created_at.tzinfo)
        self.assertIsNotNone(job.updated_at.tzinfo)

    def test_no_forbidden_fields(self):
        job = self._make_job()
        for field in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(job, field))

    def test_repr_no_secrets(self):
        job = self._make_job()
        r = repr(job)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# BackupSchedule
# ============================================================================

class TestBackupSchedule(unittest.TestCase):
    """备份调度测试"""

    def test_valid_schedule(self):
        schedule = BackupSchedule(
            schedule_id="sched-001",
            cron_expression="0 2 * * *",
        )
        self.assertEqual(schedule.schedule_id, "sched-001")
        self.assertEqual(schedule.cron_expression, "0 2 * * *")
        self.assertTrue(schedule.enabled)

    def test_frozen(self):
        schedule = BackupSchedule(
            schedule_id="sched-001",
            cron_expression="0 2 * * *",
        )
        with self.assertRaises(AttributeError):
            schedule.schedule_id = "other"

    def test_empty_schedule_id_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            BackupSchedule(schedule_id="", cron_expression="0 2 * * *")

    def test_empty_cron_rejected(self):
        with self.assertRaises(InvalidBackupJobError):
            BackupSchedule(schedule_id="s1", cron_expression="")

    def test_enabled_must_be_bool(self):
        with self.assertRaises(InvalidBackupJobError):
            BackupSchedule(schedule_id="s1", cron_expression="0 2 * * *", enabled=1)

    def test_enabled_false(self):
        schedule = BackupSchedule(
            schedule_id="s1",
            cron_expression="0 2 * * *",
            enabled=False,
        )
        self.assertFalse(schedule.enabled)

    def test_no_forbidden_fields(self):
        schedule = BackupSchedule(schedule_id="s1", cron_expression="0 2 * * *")
        for field in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(schedule, field))


# ============================================================================
# BackupPolicy
# ============================================================================

class TestBackupPolicy(unittest.TestCase):
    """备份策略测试"""

    def test_valid_policy(self):
        policy = BackupPolicy(policy_id="pol-001")
        self.assertEqual(policy.policy_id, "pol-001")
        self.assertEqual(policy.daily_retention, 7)
        self.assertEqual(policy.weekly_retention, 4)
        self.assertEqual(policy.monthly_retention, 12)

    def test_frozen(self):
        policy = BackupPolicy(policy_id="pol-001")
        with self.assertRaises(AttributeError):
            policy.policy_id = "other"

    def test_empty_policy_id_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            BackupPolicy(policy_id="")

    def test_negative_daily_retention_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            BackupPolicy(policy_id="p1", daily_retention=-1)

    def test_negative_weekly_retention_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            BackupPolicy(policy_id="p1", weekly_retention=-1)

    def test_negative_monthly_retention_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            BackupPolicy(policy_id="p1", monthly_retention=-1)

    def test_zero_retention_allowed(self):
        policy = BackupPolicy(
            policy_id="p1",
            daily_retention=0,
            weekly_retention=0,
            monthly_retention=0,
        )
        self.assertEqual(policy.daily_retention, 0)

    def test_bool_retention_rejected(self):
        with self.assertRaises(InvalidPolicyError):
            BackupPolicy(policy_id="p1", daily_retention=True)

    def test_custom_retention(self):
        policy = BackupPolicy(
            policy_id="p1",
            daily_retention=14,
            weekly_retention=8,
            monthly_retention=24,
        )
        self.assertEqual(policy.daily_retention, 14)
        self.assertEqual(policy.weekly_retention, 8)
        self.assertEqual(policy.monthly_retention, 24)

    def test_no_forbidden_fields(self):
        policy = BackupPolicy(policy_id="p1")
        for field in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(policy, field))


# ============================================================================
# BackupExecutionState
# ============================================================================

class TestBackupExecutionState(unittest.TestCase):
    """执行状态测试"""

    def test_pending(self):
        self.assertEqual(BackupExecutionState.PENDING.value, "pending")

    def test_running(self):
        self.assertEqual(BackupExecutionState.RUNNING.value, "running")

    def test_success(self):
        self.assertEqual(BackupExecutionState.SUCCESS.value, "success")

    def test_failed(self):
        self.assertEqual(BackupExecutionState.FAILED.value, "failed")

    def test_cancelled(self):
        self.assertEqual(BackupExecutionState.CANCELLED.value, "cancelled")

    def test_five_states(self):
        self.assertEqual(len(BackupExecutionState), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            BackupExecutionState("nonexistent")


# ============================================================================
# Error Model
# ============================================================================

class TestBackupErrorModel(unittest.TestCase):
    """错误模型测试"""

    def test_workflow_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise BackupWorkflowError("test")

    def test_invalid_job_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise InvalidBackupJobError("test")

    def test_invalid_policy_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise InvalidPolicyError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (BackupWorkflowError, ("test",)),
            (InvalidBackupJobError, ("test",)),
            (InvalidPolicyError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_job_no_credentials(self):
        job = BackupJob(
            job_id="j1", name="N", source_device_id="s",
            target_device_id="t", schedule_id="sc", policy_id="p",
        )
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(job, attr))

    def test_schedule_no_credentials(self):
        schedule = BackupSchedule(schedule_id="s1", cron_expression="0 2 * * *")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(schedule, attr))

    def test_policy_no_credentials(self):
        policy = BackupPolicy(policy_id="p1")
        for attr in ["password", "credential", "token", "ssh", "command"]:
            self.assertFalse(hasattr(policy, attr))

    def test_no_subprocess(self):
        import ast
        import os
        # system_process.py 合法使用 subprocess.run
        excluded = {"system_process.py"}
        backup_dir = os.path.join("backup_manager", "backup")
        for filename in os.listdir(backup_dir):
            if not filename.endswith(".py") or filename in excluded:
                continue
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
        for filename in os.listdir(backup_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(backup_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_job_repr_no_secrets(self):
        job = BackupJob(
            job_id="j1", name="N", source_device_id="s",
            target_device_id="t", schedule_id="sc", policy_id="p",
        )
        r = repr(job)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_schedule_repr_no_secrets(self):
        schedule = BackupSchedule(schedule_id="s1", cron_expression="0 2 * * *")
        r = repr(schedule)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_policy_repr_no_secrets(self):
        policy = BackupPolicy(policy_id="p1")
        r = repr(policy)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


if __name__ == "__main__":
    unittest.main()
