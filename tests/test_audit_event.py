"""
WorkOps Audit Event System Tests
Sprint040: Audit Event System Foundation

覆盖：
- AuditEventType enum
- AuditSeverity enum
- AuditEvent model
- AuditEventStore contract
- AuditQuery model
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.audit.event import AuditEventType, AuditSeverity
from backup_manager.audit.model import AuditEvent
from backup_manager.audit.store import AuditEventStore
from backup_manager.audit.query import AuditQuery
from backup_manager.audit.errors import (
    AuditError,
    InvalidAuditEventError,
    AuditEventConflictError,
    AuditEventNotFoundError,
)


# ============================================================================
# AuditEventType
# ============================================================================

class TestAuditEventType(unittest.TestCase):
    """审计事件类型测试"""

    def test_operation_created(self):
        self.assertEqual(AuditEventType.OPERATION_CREATED.value, "operation_created")

    def test_operation_started(self):
        self.assertEqual(AuditEventType.OPERATION_STARTED.value, "operation_started")

    def test_operation_completed(self):
        self.assertEqual(AuditEventType.OPERATION_COMPLETED.value, "operation_completed")

    def test_operation_failed(self):
        self.assertEqual(AuditEventType.OPERATION_FAILED.value, "operation_failed")

    def test_job_created(self):
        self.assertEqual(AuditEventType.JOB_CREATED.value, "job_created")

    def test_job_started(self):
        self.assertEqual(AuditEventType.JOB_STARTED.value, "job_started")

    def test_job_completed(self):
        self.assertEqual(AuditEventType.JOB_COMPLETED.value, "job_completed")

    def test_job_failed(self):
        self.assertEqual(AuditEventType.JOB_FAILED.value, "job_failed")

    def test_eight_types(self):
        self.assertEqual(len(AuditEventType), 8)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            AuditEventType("nonexistent")


# ============================================================================
# AuditSeverity
# ============================================================================

class TestAuditSeverity(unittest.TestCase):
    """审计严重级别测试"""

    def test_info(self):
        self.assertEqual(AuditSeverity.INFO.value, "info")

    def test_warning(self):
        self.assertEqual(AuditSeverity.WARNING.value, "warning")

    def test_error(self):
        self.assertEqual(AuditSeverity.ERROR.value, "error")

    def test_three_severities(self):
        self.assertEqual(len(AuditSeverity), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            AuditSeverity("nonexistent")


# ============================================================================
# AuditEvent
# ============================================================================

class TestAuditEvent(unittest.TestCase):
    """审计事件测试"""

    def _make_event(self, **kwargs):
        defaults = {
            "event_id": "evt-001",
            "event_type": AuditEventType.OPERATION_CREATED,
            "severity": AuditSeverity.INFO,
            "message": "Operation created",
        }
        defaults.update(kwargs)
        return AuditEvent(**defaults)

    def test_valid_event(self):
        event = self._make_event()
        self.assertEqual(event.event_id, "evt-001")
        self.assertEqual(event.event_type, AuditEventType.OPERATION_CREATED)
        self.assertEqual(event.severity, AuditSeverity.INFO)
        self.assertEqual(event.message, "Operation created")

    def test_frozen(self):
        event = self._make_event()
        with self.assertRaises(AttributeError):
            event.event_id = "other"

    def test_slots(self):
        event = self._make_event()
        with self.assertRaises(AttributeError):
            event.__dict__

    def test_empty_event_id_rejected(self):
        with self.assertRaises(InvalidAuditEventError):
            self._make_event(event_id="")

    def test_empty_message_rejected(self):
        with self.assertRaises(InvalidAuditEventError):
            self._make_event(message="")

    def test_invalid_event_type_rejected(self):
        with self.assertRaises(InvalidAuditEventError):
            self._make_event(event_type="operation_created")

    def test_invalid_severity_rejected(self):
        with self.assertRaises(InvalidAuditEventError):
            self._make_event(severity="info")

    def test_timezone_aware(self):
        event = self._make_event()
        self.assertIsNotNone(event.created_at.tzinfo)

    def test_with_operation_id(self):
        event = self._make_event(operation_id="op-001")
        self.assertEqual(event.operation_id, "op-001")

    def test_with_job_id(self):
        event = self._make_event(job_id="job-001")
        self.assertEqual(event.job_id, "job-001")

    def test_operation_id_none_default(self):
        event = self._make_event()
        self.assertIsNone(event.operation_id)

    def test_job_id_none_default(self):
        event = self._make_event()
        self.assertIsNone(event.job_id)

    def test_no_forbidden_fields(self):
        event = self._make_event()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "command", "ip", "hostname", "stdout", "stderr"]:
            self.assertFalse(hasattr(event, attr))

    def test_repr_no_secrets(self):
        event = self._make_event()
        r = repr(event)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# AuditEventStore Contract
# ============================================================================

class TestAuditEventStoreContract(unittest.TestCase):
    """审计事件存储契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AuditEventStore, ABC))

    def test_has_append(self):
        self.assertTrue(hasattr(AuditEventStore, "append"))

    def test_has_get(self):
        self.assertTrue(hasattr(AuditEventStore, "get"))

    def test_has_list(self):
        self.assertTrue(hasattr(AuditEventStore, "list"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AuditEventStore()

    def test_concrete_subclass(self):
        class MockStore(AuditEventStore):
            def __init__(self):
                self._events = {}
            def append(self, event):
                self._events[event.event_id] = event
            def get(self, event_id):
                return self._events[event_id]
            def list(self):
                return list(self._events.values())
        store = MockStore()
        event = AuditEvent(
            event_id="e1", event_type=AuditEventType.OPERATION_CREATED,
            severity=AuditSeverity.INFO, message="test",
        )
        store.append(event)
        got = store.get("e1")
        self.assertEqual(got.event_id, "e1")
        self.assertEqual(len(store.list()), 1)

    def test_missing_append(self):
        class BadStore(AuditEventStore):
            def get(self, event_id):
                pass
            def list(self):
                pass
        with self.assertRaises(TypeError):
            BadStore()

    def test_missing_get(self):
        class BadStore(AuditEventStore):
            def append(self, event):
                pass
            def list(self):
                pass
        with self.assertRaises(TypeError):
            BadStore()

    def test_missing_list(self):
        class BadStore(AuditEventStore):
            def append(self, event):
                pass
            def get(self, event_id):
                pass
        with self.assertRaises(TypeError):
            BadStore()


# ============================================================================
# AuditQuery
# ============================================================================

class TestAuditQuery(unittest.TestCase):
    """审计查询测试"""

    def test_valid_query(self):
        query = AuditQuery(
            event_type=AuditEventType.OPERATION_CREATED,
            operation_id="op-001",
            job_id="job-001",
        )
        self.assertEqual(query.event_type, AuditEventType.OPERATION_CREATED)
        self.assertEqual(query.operation_id, "op-001")
        self.assertEqual(query.job_id, "job-001")

    def test_frozen(self):
        query = AuditQuery(event_type=AuditEventType.OPERATION_CREATED)
        with self.assertRaises(AttributeError):
            query.event_type = None

    def test_slots(self):
        query = AuditQuery()
        with self.assertRaises(AttributeError):
            query.__dict__

    def test_defaults_none(self):
        query = AuditQuery()
        self.assertIsNone(query.event_type)
        self.assertIsNone(query.operation_id)
        self.assertIsNone(query.job_id)

    def test_no_forbidden_fields(self):
        query = AuditQuery()
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(query, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestAuditErrors(unittest.TestCase):
    """错误模型测试"""

    def test_audit_error(self):
        with self.assertRaises(AuditError):
            raise AuditError("test")

    def test_invalid_event_error(self):
        with self.assertRaises(AuditError):
            raise InvalidAuditEventError("test")

    def test_conflict_error(self):
        exc = AuditEventConflictError("e1")
        self.assertIn("e1", str(exc))

    def test_not_found_error(self):
        exc = AuditEventNotFoundError("e1")
        self.assertIn("e1", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (AuditError, ("test",)),
            (InvalidAuditEventError, ("test",)),
            (AuditEventConflictError, ("e1",)),
            (AuditEventNotFoundError, ("e1",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_event_no_credentials(self):
        event = AuditEvent(
            event_id="e1", event_type=AuditEventType.OPERATION_CREATED,
            severity=AuditSeverity.INFO, message="test",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(event, attr))

    def test_query_no_credentials(self):
        query = AuditQuery()
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(query, attr))

    def test_no_subprocess(self):
        import ast
        import os
        audit_dir = os.path.join("backup_manager", "audit")
        for filename in os.listdir(audit_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(audit_dir, filename)
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
        audit_dir = os.path.join("backup_manager", "audit")
        for filename in os.listdir(audit_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(audit_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_store_lifecycle(self):
        """完整存储生命周期"""
        class MockStore(AuditEventStore):
            def __init__(self):
                self._events = {}
            def append(self, event):
                self._events[event.event_id] = event
            def get(self, event_id):
                return self._events[event_id]
            def list(self):
                return list(self._events.values())
        store = MockStore()
        event = AuditEvent(
            event_id="e1", event_type=AuditEventType.OPERATION_CREATED,
            severity=AuditSeverity.INFO, message="test",
        )
        store.append(event)
        got = store.get("e1")
        self.assertEqual(got.event_id, "e1")
        self.assertEqual(len(store.list()), 1)


if __name__ == "__main__":
    unittest.main()
