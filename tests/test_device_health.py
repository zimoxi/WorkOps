"""
WorkOps Device Health Monitoring Tests
Sprint043: Device Health Monitoring Foundation

覆盖：
- HealthStatus enum
- HealthCheckType enum
- HealthCheckRequest model
- HealthResult model
- HealthChecker contract
- HealthHistory model
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.health.status import HealthStatus, HealthCheckType
from backup_manager.health.request import HealthCheckRequest
from backup_manager.health.result import HealthResult
from backup_manager.health.checker import HealthChecker
from backup_manager.health.history import HealthHistory
from backup_manager.health.errors import (
    HealthError,
    InvalidHealthRequestError,
    HealthCheckConflictError,
    HealthCheckNotFoundError,
)


# ============================================================================
# HealthStatus
# ============================================================================

class TestHealthStatus(unittest.TestCase):
    """健康状态测试"""

    def test_unknown(self):
        self.assertEqual(HealthStatus.UNKNOWN.value, "unknown")

    def test_healthy(self):
        self.assertEqual(HealthStatus.HEALTHY.value, "healthy")

    def test_warning(self):
        self.assertEqual(HealthStatus.WARNING.value, "warning")

    def test_critical(self):
        self.assertEqual(HealthStatus.CRITICAL.value, "critical")

    def test_offline(self):
        self.assertEqual(HealthStatus.OFFLINE.value, "offline")

    def test_five_statuses(self):
        self.assertEqual(len(HealthStatus), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            HealthStatus("nonexistent")


# ============================================================================
# HealthCheckType
# ============================================================================

class TestHealthCheckType(unittest.TestCase):
    """健康检查类型测试"""

    def test_system(self):
        self.assertEqual(HealthCheckType.SYSTEM.value, "system")

    def test_storage(self):
        self.assertEqual(HealthCheckType.STORAGE.value, "storage")

    def test_network(self):
        self.assertEqual(HealthCheckType.NETWORK.value, "network")

    def test_service(self):
        self.assertEqual(HealthCheckType.SERVICE.value, "service")

    def test_four_types(self):
        self.assertEqual(len(HealthCheckType), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            HealthCheckType("nonexistent")


# ============================================================================
# HealthCheckRequest
# ============================================================================

class TestHealthCheckRequest(unittest.TestCase):
    """健康检查请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "check_id": "chk-001",
            "device_id": "dev-001",
            "check_type": HealthCheckType.SYSTEM,
        }
        defaults.update(kwargs)
        return HealthCheckRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.check_id, "chk-001")
        self.assertEqual(req.device_id, "dev-001")
        self.assertEqual(req.check_type, HealthCheckType.SYSTEM)

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.check_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_check_id_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            self._make_request(check_id="")

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            self._make_request(device_id="")

    def test_invalid_check_type_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            self._make_request(check_type="system")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_all_check_types(self):
        for ct in HealthCheckType:
            req = self._make_request(check_type=ct)
            self.assertEqual(req.check_type, ct)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "command", "ip", "hostname"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# HealthResult
# ============================================================================

class TestHealthResult(unittest.TestCase):
    """健康检查结果测试"""

    def test_valid_result(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        self.assertEqual(result.check_id, "chk-001")
        self.assertTrue(result.success)
        self.assertEqual(result.status, HealthStatus.HEALTHY)

    def test_frozen(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.check_id = "other"

    def test_slots(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_check_id_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthResult(
                check_id="", status=HealthStatus.HEALTHY,
                success=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthResult(
                check_id="chk-001", status="healthy",
                success=True, message="ok",
            )

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthResult(
                check_id="chk-001", status=HealthStatus.HEALTHY,
                success=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthResult(
                check_id="chk-001", status=HealthStatus.HEALTHY,
                success=True, message=123,
            )

    def test_timezone_aware(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        self.assertIsNotNone(result.checked_at.tzinfo)

    def test_all_health_statuses(self):
        for status in HealthStatus:
            result = HealthResult(
                check_id="chk-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_no_forbidden_fields(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# HealthChecker Contract
# ============================================================================

class TestHealthCheckerContract(unittest.TestCase):
    """健康检查器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(HealthChecker, ABC))

    def test_has_check(self):
        self.assertTrue(hasattr(HealthChecker, "check"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            HealthChecker()

    def test_concrete_subclass(self):
        class MockChecker(HealthChecker):
            def check(self, request):
                return HealthResult(
                    check_id=request.check_id,
                    status=HealthStatus.HEALTHY,
                    success=True, message="ok",
                )
        checker = MockChecker()
        req = HealthCheckRequest(
            check_id="chk-001", device_id="dev-001",
            check_type=HealthCheckType.SYSTEM,
        )
        result = checker.check(req)
        self.assertTrue(result.success)

    def test_missing_check(self):
        class BadChecker(HealthChecker):
            pass
        with self.assertRaises(TypeError):
            BadChecker()


# ============================================================================
# HealthHistory
# ============================================================================

class TestHealthHistory(unittest.TestCase):
    """健康历史测试"""

    def test_valid_history(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        self.assertEqual(history.check_id, "chk-001")
        self.assertEqual(history.device_id, "dev-001")
        self.assertEqual(history.status, HealthStatus.HEALTHY)

    def test_frozen(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        with self.assertRaises(AttributeError):
            history.check_id = "other"

    def test_slots(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        with self.assertRaises(AttributeError):
            history.__dict__

    def test_empty_check_id_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthHistory(check_id="", device_id="dev-001", status=HealthStatus.HEALTHY)

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthHistory(check_id="chk-001", device_id="", status=HealthStatus.HEALTHY)

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidHealthRequestError):
            HealthHistory(check_id="chk-001", device_id="dev-001", status="healthy")

    def test_timezone_aware(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        self.assertIsNotNone(history.checked_at.tzinfo)

    def test_no_forbidden_fields(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(history, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestHealthErrors(unittest.TestCase):
    """错误模型测试"""

    def test_health_error(self):
        with self.assertRaises(HealthError):
            raise HealthError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(HealthError):
            raise InvalidHealthRequestError("test")

    def test_conflict_error(self):
        exc = HealthCheckConflictError("chk-001")
        self.assertIn("chk-001", str(exc))

    def test_not_found_error(self):
        exc = HealthCheckNotFoundError("chk-001")
        self.assertIn("chk-001", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (HealthError, ("test",)),
            (InvalidHealthRequestError, ("test",)),
            (HealthCheckConflictError, ("chk-001",)),
            (HealthCheckNotFoundError, ("chk-001",)),
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
        req = HealthCheckRequest(
            check_id="chk-001", device_id="dev-001",
            check_type=HealthCheckType.SYSTEM,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_history_no_credentials(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(history, attr))

    def test_no_subprocess(self):
        import ast
        import os
        health_dir = os.path.join("backup_manager", "health")
        for filename in os.listdir(health_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(health_dir, filename)
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
        health_dir = os.path.join("backup_manager", "health")
        for filename in os.listdir(health_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(health_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_checker_lifecycle(self):
        """完整检查器生命周期"""
        class MockChecker(HealthChecker):
            def check(self, request):
                return HealthResult(
                    check_id=request.check_id,
                    status=HealthStatus.HEALTHY,
                    success=True, message="ok",
                )
        checker = MockChecker()
        req = HealthCheckRequest(
            check_id="chk-001", device_id="dev-001",
            check_type=HealthCheckType.SYSTEM,
        )
        result = checker.check(req)
        self.assertTrue(result.success)
        self.assertEqual(result.status, HealthStatus.HEALTHY)


# ============================================================================
# Extended Tests
# ============================================================================

class TestHealthExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidHealthRequestError, HealthError))
        self.assertTrue(issubclass(HealthCheckConflictError, HealthError))
        self.assertTrue(issubclass(HealthCheckNotFoundError, HealthError))

    def test_request_repr_no_secrets(self):
        req = HealthCheckRequest(
            check_id="chk-001", device_id="dev-001",
            check_type=HealthCheckType.SYSTEM,
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.HEALTHY,
            success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_history_repr_no_secrets(self):
        history = HealthHistory(
            check_id="chk-001", device_id="dev-001",
            status=HealthStatus.HEALTHY,
        )
        r = repr(history)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_critical_status_result(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.CRITICAL,
            success=False, message="disk full",
        )
        self.assertEqual(result.status, HealthStatus.CRITICAL)
        self.assertFalse(result.success)

    def test_offline_status_result(self):
        result = HealthResult(
            check_id="chk-001", status=HealthStatus.OFFLINE,
            success=False, message="unreachable",
        )
        self.assertEqual(result.status, HealthStatus.OFFLINE)


if __name__ == "__main__":
    unittest.main()
