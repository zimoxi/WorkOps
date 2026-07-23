"""
WorkOps Job Scheduler Tests
Sprint039: Job Scheduler Foundation

覆盖：
- JobType enum
- JobStatus validation
- Job model
- JobScheduler contract
- JobWorker contract
- JobHistory model
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.jobs.status import JobType
from backup_manager.jobs.model import Job, JobStatus
from backup_manager.jobs.scheduler import JobScheduler
from backup_manager.jobs.worker import JobWorker
from backup_manager.jobs.history import JobHistory
from backup_manager.jobs.errors import (
    JobError,
    InvalidJobError,
    JobConflictError,
    JobNotFoundError,
)


# ============================================================================
# JobType
# ============================================================================

class TestJobType(unittest.TestCase):
    """作业类型测试"""

    def test_operation(self):
        self.assertEqual(JobType.OPERATION.value, "operation")

    def test_one_type(self):
        self.assertEqual(len(JobType), 1)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            JobType("nonexistent")


# ============================================================================
# JobStatus
# ============================================================================

class TestJobStatus(unittest.TestCase):
    """作业状态测试"""

    def test_created(self):
        self.assertEqual(JobStatus.CREATED, "created")

    def test_queued(self):
        self.assertEqual(JobStatus.QUEUED, "queued")

    def test_running(self):
        self.assertEqual(JobStatus.RUNNING, "running")

    def test_success(self):
        self.assertEqual(JobStatus.SUCCESS, "success")

    def test_failed(self):
        self.assertEqual(JobStatus.FAILED, "failed")

    def test_cancelled(self):
        self.assertEqual(JobStatus.CANCELLED, "cancelled")

    def test_six_statuses(self):
        self.assertEqual(len(JobStatus._VALID), 6)

    def test_validate_valid(self):
        for status in JobStatus._VALID:
            self.assertEqual(JobStatus.validate(status), status)

    def test_validate_invalid(self):
        with self.assertRaises(InvalidJobError):
            JobStatus.validate("nonexistent")


# ============================================================================
# Job Model
# ============================================================================

class TestJobModel(unittest.TestCase):
    """作业模型测试"""

    def _make_job(self, **kwargs):
        defaults = {
            "job_id": "job-001",
            "job_type": JobType.OPERATION,
            "operation_id": "op-001",
        }
        defaults.update(kwargs)
        return Job(**defaults)

    def test_valid_job(self):
        job = self._make_job()
        self.assertEqual(job.job_id, "job-001")
        self.assertEqual(job.job_type, JobType.OPERATION)
        self.assertEqual(job.operation_id, "op-001")
        self.assertEqual(job.status, JobStatus.CREATED)

    def test_frozen(self):
        job = self._make_job()
        with self.assertRaises(AttributeError):
            job.job_id = "other"

    def test_slots(self):
        job = self._make_job()
        with self.assertRaises(AttributeError):
            job.__dict__

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidJobError):
            self._make_job(job_id="")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidJobError):
            self._make_job(operation_id="")

    def test_invalid_job_type_rejected(self):
        with self.assertRaises(InvalidJobError):
            self._make_job(job_type="operation")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidJobError):
            self._make_job(status="invalid")

    def test_timezone_aware(self):
        job = self._make_job()
        self.assertIsNotNone(job.created_at.tzinfo)

    def test_custom_status(self):
        job = self._make_job(status=JobStatus.QUEUED)
        self.assertEqual(job.status, JobStatus.QUEUED)

    def test_no_forbidden_fields(self):
        job = self._make_job()
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(job, attr))

    def test_repr_no_secrets(self):
        job = self._make_job()
        r = repr(job)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# JobScheduler Contract
# ============================================================================

class TestJobSchedulerContract(unittest.TestCase):
    """调度器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(JobScheduler, ABC))

    def test_has_submit(self):
        self.assertTrue(hasattr(JobScheduler, "submit"))

    def test_has_get(self):
        self.assertTrue(hasattr(JobScheduler, "get"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            JobScheduler()

    def test_concrete_subclass(self):
        class MockScheduler(JobScheduler):
            def __init__(self):
                self._jobs = {}
            def submit(self, job):
                self._jobs[job.job_id] = job
            def get(self, job_id):
                return self._jobs[job_id]
        scheduler = MockScheduler()
        job = Job(job_id="j1", job_type=JobType.OPERATION, operation_id="op1")
        scheduler.submit(job)
        got = scheduler.get("j1")
        self.assertEqual(got.job_id, "j1")

    def test_missing_submit(self):
        class BadScheduler(JobScheduler):
            def get(self, job_id):
                pass
        with self.assertRaises(TypeError):
            BadScheduler()

    def test_missing_get(self):
        class BadScheduler(JobScheduler):
            def submit(self, job):
                pass
        with self.assertRaises(TypeError):
            BadScheduler()


# ============================================================================
# JobWorker Contract
# ============================================================================

class TestJobWorkerContract(unittest.TestCase):
    """工作器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(JobWorker, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(JobWorker, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            JobWorker()

    def test_concrete_subclass(self):
        class MockWorker(JobWorker):
            def execute(self, job):
                return {"success": True, "message": "done"}
        worker = MockWorker()
        job = Job(job_id="j1", job_type=JobType.OPERATION, operation_id="op1")
        result = worker.execute(job)
        self.assertTrue(result["success"])

    def test_missing_execute(self):
        class BadWorker(JobWorker):
            pass
        with self.assertRaises(TypeError):
            BadWorker()


# ============================================================================
# JobHistory
# ============================================================================

class TestJobHistory(unittest.TestCase):
    """作业历史测试"""

    def test_valid_history(self):
        history = JobHistory(job_id="j1", status=JobStatus.SUCCESS)
        self.assertEqual(history.job_id, "j1")
        self.assertEqual(history.status, JobStatus.SUCCESS)

    def test_frozen(self):
        history = JobHistory(job_id="j1", status=JobStatus.SUCCESS)
        with self.assertRaises(AttributeError):
            history.job_id = "other"

    def test_slots(self):
        history = JobHistory(job_id="j1", status=JobStatus.SUCCESS)
        with self.assertRaises(AttributeError):
            history.__dict__

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidJobError):
            JobHistory(job_id="", status=JobStatus.SUCCESS)

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidJobError):
            JobHistory(job_id="j1", status="invalid")

    def test_timezone_aware(self):
        history = JobHistory(job_id="j1", status=JobStatus.SUCCESS)
        self.assertIsNotNone(history.created_at.tzinfo)
        self.assertIsNotNone(history.updated_at.tzinfo)

    def test_no_forbidden_fields(self):
        history = JobHistory(job_id="j1", status=JobStatus.SUCCESS)
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(history, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestJobErrors(unittest.TestCase):
    """错误模型测试"""

    def test_job_error(self):
        with self.assertRaises(JobError):
            raise JobError("test")

    def test_invalid_job_error(self):
        with self.assertRaises(JobError):
            raise InvalidJobError("test")

    def test_conflict_error(self):
        exc = JobConflictError("j1")
        self.assertIn("j1", str(exc))

    def test_not_found_error(self):
        exc = JobNotFoundError("j1")
        self.assertIn("j1", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (JobError, ("test",)),
            (InvalidJobError, ("test",)),
            (JobConflictError, ("j1",)),
            (JobNotFoundError, ("j1",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_job_no_credentials(self):
        job = Job(job_id="j1", job_type=JobType.OPERATION, operation_id="op1")
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(job, attr))

    def test_history_no_credentials(self):
        history = JobHistory(job_id="j1", status=JobStatus.SUCCESS)
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(history, attr))

    def test_no_subprocess(self):
        import ast
        import os
        jobs_dir = os.path.join("backup_manager", "jobs")
        for filename in os.listdir(jobs_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(jobs_dir, filename)
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
        jobs_dir = os.path.join("backup_manager", "jobs")
        for filename in os.listdir(jobs_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(jobs_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_scheduler_lifecycle(self):
        """完整调度器生命周期"""
        class MockScheduler(JobScheduler):
            def __init__(self):
                self._jobs = {}
            def submit(self, job):
                self._jobs[job.job_id] = job
            def get(self, job_id):
                return self._jobs[job_id]
        scheduler = MockScheduler()
        job = Job(job_id="j1", job_type=JobType.OPERATION, operation_id="op1")
        scheduler.submit(job)
        got = scheduler.get("j1")
        self.assertEqual(got.job_id, "j1")


if __name__ == "__main__":
    unittest.main()
