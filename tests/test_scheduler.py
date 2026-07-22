"""
WorkOps Backup Scheduler Tests
Sprint035: Backup Scheduler Foundation

覆盖：
- BackupScheduleBinding validation
- SchedulerTrigger creation
- SchedulerService lifecycle
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.scheduler.models import BackupScheduleBinding
from backup_manager.scheduler.trigger import SchedulerTrigger
from backup_manager.scheduler.service import SchedulerService
from backup_manager.scheduler.errors import SchedulerError, InvalidScheduleError


# ============================================================================
# BackupScheduleBinding
# ============================================================================

class TestBackupScheduleBinding(unittest.TestCase):
    """调度绑定测试"""

    def test_valid_binding(self):
        binding = BackupScheduleBinding(
            binding_id="b1",
            job_id="j1",
            cron_expression="0 2 * * *",
        )
        self.assertEqual(binding.binding_id, "b1")
        self.assertEqual(binding.job_id, "j1")
        self.assertEqual(binding.cron_expression, "0 2 * * *")
        self.assertTrue(binding.enabled)

    def test_frozen(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        with self.assertRaises(AttributeError):
            binding.binding_id = "other"

    def test_slots(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        with self.assertRaises(AttributeError):
            binding.__dict__

    def test_empty_binding_id_rejected(self):
        with self.assertRaises(InvalidScheduleError):
            BackupScheduleBinding(binding_id="", job_id="j1", cron_expression="0 2 * * *")

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidScheduleError):
            BackupScheduleBinding(binding_id="b1", job_id="", cron_expression="0 2 * * *")

    def test_empty_cron_rejected(self):
        with self.assertRaises(InvalidScheduleError):
            BackupScheduleBinding(binding_id="b1", job_id="j1", cron_expression="")

    def test_enabled_must_be_bool(self):
        with self.assertRaises(InvalidScheduleError):
            BackupScheduleBinding(binding_id="b1", job_id="j1", cron_expression="0 2 * * *", enabled=1)

    def test_enabled_false(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *", enabled=False,
        )
        self.assertFalse(binding.enabled)

    def test_created_at_timezone_aware(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        self.assertIsNotNone(binding.created_at)
        self.assertIsNotNone(binding.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(binding, attr))

    def test_repr_no_secrets(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        r = repr(binding)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# SchedulerTrigger
# ============================================================================

class TestSchedulerTrigger(unittest.TestCase):
    """调度触发器测试"""

    def test_valid_trigger(self):
        now = datetime.now(timezone.utc)
        trigger = SchedulerTrigger(
            trigger_id="t1", binding_id="b1", trigger_time=now,
        )
        self.assertEqual(trigger.trigger_id, "t1")
        self.assertEqual(trigger.binding_id, "b1")
        self.assertEqual(trigger.trigger_time, now)

    def test_frozen(self):
        now = datetime.now(timezone.utc)
        trigger = SchedulerTrigger(trigger_id="t1", binding_id="b1", trigger_time=now)
        with self.assertRaises(AttributeError):
            trigger.trigger_id = "other"

    def test_empty_trigger_id_rejected(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(InvalidScheduleError):
            SchedulerTrigger(trigger_id="", binding_id="b1", trigger_time=now)

    def test_empty_binding_id_rejected(self):
        now = datetime.now(timezone.utc)
        with self.assertRaises(InvalidScheduleError):
            SchedulerTrigger(trigger_id="t1", binding_id="", trigger_time=now)

    def test_trigger_time_must_be_datetime(self):
        with self.assertRaises(InvalidScheduleError):
            SchedulerTrigger(trigger_id="t1", binding_id="b1", trigger_time="not_dt")

    def test_create_factory(self):
        trigger = SchedulerTrigger.create(binding_id="b1")
        self.assertIsNotNone(trigger.trigger_id)
        self.assertEqual(trigger.binding_id, "b1")
        self.assertIsNotNone(trigger.trigger_time)
        self.assertIsNotNone(trigger.trigger_time.tzinfo)

    def test_create_unique_ids(self):
        t1 = SchedulerTrigger.create(binding_id="b1")
        t2 = SchedulerTrigger.create(binding_id="b1")
        self.assertNotEqual(t1.trigger_id, t2.trigger_id)

    def test_no_forbidden_fields(self):
        now = datetime.now(timezone.utc)
        trigger = SchedulerTrigger(trigger_id="t1", binding_id="b1", trigger_time=now)
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(trigger, attr))


# ============================================================================
# SchedulerService
# ============================================================================

class TestSchedulerService(unittest.TestCase):
    """调度服务测试"""

    def setUp(self):
        self.service = SchedulerService()

    def test_create_binding(self):
        binding = self.service.create_binding("j1", "0 2 * * *")
        self.assertEqual(binding.job_id, "j1")
        self.assertEqual(binding.cron_expression, "0 2 * * *")
        self.assertTrue(binding.enabled)

    def test_get_binding(self):
        binding = self.service.create_binding("j1", "0 2 * * *")
        got = self.service.get_binding(binding.binding_id)
        self.assertEqual(got.binding_id, binding.binding_id)

    def test_get_binding_not_found(self):
        with self.assertRaises(SchedulerError):
            self.service.get_binding("nonexistent")

    def test_list_bindings(self):
        self.service.create_binding("j1", "0 2 * * *")
        self.service.create_binding("j2", "0 3 * * *")
        self.assertEqual(len(self.service.list_bindings()), 2)

    def test_evaluate_returns_enabled(self):
        self.service.create_binding("j1", "0 2 * * *", enabled=True)
        self.service.create_binding("j2", "0 3 * * *", enabled=False)
        due = self.service.evaluate()
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0].job_id, "j1")

    def test_evaluate_empty(self):
        self.assertEqual(self.service.evaluate(), [])

    def test_create_trigger(self):
        binding = self.service.create_binding("j1", "0 2 * * *")
        trigger = self.service.create_trigger(binding.binding_id)
        self.assertEqual(trigger.binding_id, binding.binding_id)
        self.assertIsNotNone(trigger.trigger_id)

    def test_create_trigger_not_found(self):
        with self.assertRaises(SchedulerError):
            self.service.create_trigger("nonexistent")

    def test_get_trigger(self):
        binding = self.service.create_binding("j1", "0 2 * * *")
        trigger = self.service.create_trigger(binding.binding_id)
        got = self.service.get_trigger(trigger.trigger_id)
        self.assertEqual(got.trigger_id, trigger.trigger_id)

    def test_get_trigger_not_found(self):
        with self.assertRaises(SchedulerError):
            self.service.get_trigger("nonexistent")

    def test_list_triggers(self):
        binding = self.service.create_binding("j1", "0 2 * * *")
        self.service.create_trigger(binding.binding_id)
        self.service.create_trigger(binding.binding_id)
        self.assertEqual(len(self.service.list_triggers()), 2)

    def test_no_real_execution(self):
        """确认没有真实执行方法"""
        for method in ["run_scheduler", "start_daemon", "execute"]:
            self.assertFalse(hasattr(self.service, method))

    def test_list_bindings_empty(self):
        self.assertEqual(self.service.list_bindings(), [])

    def test_list_triggers_empty(self):
        self.assertEqual(self.service.list_triggers(), [])


# ============================================================================
# Error Model
# ============================================================================

class TestSchedulerErrors(unittest.TestCase):
    """错误模型测试"""

    def test_scheduler_error(self):
        with self.assertRaises(SchedulerError):
            raise SchedulerError("test")

    def test_invalid_schedule_error(self):
        with self.assertRaises(SchedulerError):
            raise InvalidScheduleError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (SchedulerError, ("test",)),
            (InvalidScheduleError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_binding_no_credentials(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(binding, attr))

    def test_trigger_no_credentials(self):
        now = datetime.now(timezone.utc)
        trigger = SchedulerTrigger(trigger_id="t1", binding_id="b1", trigger_time=now)
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(trigger, attr))

    def test_service_no_credentials(self):
        service = SchedulerService()
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(service, attr))

    def test_no_subprocess(self):
        import ast
        import os
        scheduler_dir = os.path.join("backup_manager", "scheduler")
        for filename in os.listdir(scheduler_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(scheduler_dir, filename)
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
        scheduler_dir = os.path.join("backup_manager", "scheduler")
        for filename in os.listdir(scheduler_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(scheduler_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_binding_repr_no_secrets(self):
        binding = BackupScheduleBinding(
            binding_id="b1", job_id="j1", cron_expression="0 2 * * *",
        )
        r = repr(binding)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_trigger_repr_no_secrets(self):
        now = datetime.now(timezone.utc)
        trigger = SchedulerTrigger(trigger_id="t1", binding_id="b1", trigger_time=now)
        r = repr(trigger)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# Extended Service Tests
# ============================================================================

class TestSchedulerServiceExtended(unittest.TestCase):
    """调度服务扩展测试"""

    def test_create_multiple_bindings(self):
        service = SchedulerService()
        for i in range(5):
            service.create_binding(f"j{i}", "0 2 * * *")
        self.assertEqual(len(service.list_bindings()), 5)

    def test_create_multiple_triggers(self):
        service = SchedulerService()
        binding = service.create_binding("j1", "0 2 * * *")
        for i in range(3):
            service.create_trigger(binding.binding_id)
        self.assertEqual(len(service.list_triggers()), 3)

    def test_evaluate_all_disabled(self):
        service = SchedulerService()
        service.create_binding("j1", "0 2 * * *", enabled=False)
        service.create_binding("j2", "0 3 * * *", enabled=False)
        self.assertEqual(len(service.evaluate()), 0)

    def test_evaluate_all_enabled(self):
        service = SchedulerService()
        service.create_binding("j1", "0 2 * * *", enabled=True)
        service.create_binding("j2", "0 3 * * *", enabled=True)
        self.assertEqual(len(service.evaluate()), 2)

    def test_trigger_has_timezone(self):
        service = SchedulerService()
        binding = service.create_binding("j1", "0 2 * * *")
        trigger = service.create_trigger(binding.binding_id)
        self.assertIsNotNone(trigger.trigger_time.tzinfo)

    def test_binding_created_at_auto(self):
        service = SchedulerService()
        binding = service.create_binding("j1", "0 2 * * *")
        self.assertIsNotNone(binding.created_at)
        self.assertIsNotNone(binding.created_at.tzinfo)

    def test_error_messages_safe(self):
        try:
            raise SchedulerError("test")
        except SchedulerError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())


if __name__ == "__main__":
    unittest.main()
