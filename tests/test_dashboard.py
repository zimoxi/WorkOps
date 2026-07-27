"""
WorkOps Web Dashboard Tests
Sprint073: Web Dashboard Foundation

覆盖：
- DashboardStatus enum
- DashboardViewModel validation
- RuntimeOverview validation
- BackupOverview validation
- RestoreOverview validation
- DashboardService contract
- DashboardRoutes contract
- Error model
- Security boundary
"""

import unittest

from backup_manager.dashboard.models import (
    DashboardStatus,
    DashboardViewModel,
    RuntimeOverview,
    BackupOverview,
    RestoreOverview,
)
from backup_manager.dashboard.service import DashboardService
from backup_manager.dashboard.routes import DashboardRoutes
from backup_manager.dashboard.providers.health_provider import HealthSummary
from backup_manager.dashboard.providers.metrics_provider import MetricsSummary
from backup_manager.dashboard.providers.audit_provider import AuditSummary
from backup_manager.dashboard.errors import (
    DashboardError,
    DashboardUnavailableError,
    InvalidDashboardRequestError,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_view_model(**kwargs):
    defaults = {
        "system_name": "WorkOps",
        "status": DashboardStatus.ONLINE,
        "runtime_count": 3,
    }
    defaults.update(kwargs)
    return DashboardViewModel(**defaults)


def _make_runtime_overview(**kwargs):
    defaults = {
        "runtime_name": "linux-ssh",
        "connected": True,
        "message": "connected",
    }
    defaults.update(kwargs)
    return RuntimeOverview(**defaults)


def _make_backup_overview(**kwargs):
    defaults = {"total": 10, "successful": 8, "failed": 2}
    defaults.update(kwargs)
    return BackupOverview(**defaults)


def _make_restore_overview(**kwargs):
    defaults = {"total": 5, "successful": 4, "failed": 1}
    defaults.update(kwargs)
    return RestoreOverview(**defaults)


# ============================================================================
# DashboardStatus
# ============================================================================

class TestDashboardStatus(unittest.TestCase):
    """仪表盘状态测试"""

    def test_online(self):
        self.assertEqual(DashboardStatus.ONLINE.value, "online")

    def test_degraded(self):
        self.assertEqual(DashboardStatus.DEGRADED.value, "degraded")

    def test_offline(self):
        self.assertEqual(DashboardStatus.OFFLINE.value, "offline")

    def test_three_statuses(self):
        self.assertEqual(len(DashboardStatus), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            DashboardStatus("nonexistent")


# ============================================================================
# DashboardViewModel
# ============================================================================

class TestDashboardViewModel(unittest.TestCase):
    """仪表盘视图模型测试"""

    def test_valid_model(self):
        model = _make_view_model()
        self.assertEqual(model.system_name, "WorkOps")
        self.assertEqual(model.status, DashboardStatus.ONLINE)
        self.assertEqual(model.runtime_count, 3)

    def test_frozen(self):
        model = _make_view_model()
        with self.assertRaises(AttributeError):
            model.system_name = "other"

    def test_slots(self):
        model = _make_view_model()
        with self.assertRaises(AttributeError):
            model.__dict__

    def test_empty_system_name_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_view_model(system_name="")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_view_model(status="online")

    def test_negative_runtime_count_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_view_model(runtime_count=-1)

    def test_zero_runtime_count_allowed(self):
        model = _make_view_model(runtime_count=0)
        self.assertEqual(model.runtime_count, 0)

    def test_timezone_aware(self):
        model = _make_view_model()
        self.assertIsNotNone(model.created_at.tzinfo)

    def test_all_statuses(self):
        for status in DashboardStatus:
            model = _make_view_model(status=status)
            self.assertEqual(model.status, status)

    def test_no_forbidden_fields(self):
        model = _make_view_model()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(model, attr))

    def test_repr_no_secrets(self):
        model = _make_view_model()
        r = repr(model)
        for term in ["password", "secret", "token", "credential", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RuntimeOverview
# ============================================================================

class TestRuntimeOverview(unittest.TestCase):
    """运行时概览测试"""

    def test_valid_overview(self):
        overview = _make_runtime_overview()
        self.assertEqual(overview.runtime_name, "linux-ssh")
        self.assertTrue(overview.connected)
        self.assertEqual(overview.message, "connected")

    def test_frozen(self):
        overview = _make_runtime_overview()
        with self.assertRaises(AttributeError):
            overview.runtime_name = "other"

    def test_slots(self):
        overview = _make_runtime_overview()
        with self.assertRaises(AttributeError):
            overview.__dict__

    def test_empty_runtime_name_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_runtime_overview(runtime_name="")

    def test_connected_must_be_bool(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_runtime_overview(connected=1)

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_runtime_overview(message=123)

    def test_disconnected_overview(self):
        overview = _make_runtime_overview(connected=False, message="disconnected")
        self.assertFalse(overview.connected)

    def test_no_forbidden_fields(self):
        overview = _make_runtime_overview()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(overview, attr))


# ============================================================================
# BackupOverview
# ============================================================================

class TestBackupOverview(unittest.TestCase):
    """备份概览测试"""

    def test_valid_overview(self):
        overview = _make_backup_overview()
        self.assertEqual(overview.total, 10)
        self.assertEqual(overview.successful, 8)
        self.assertEqual(overview.failed, 2)

    def test_frozen(self):
        overview = _make_backup_overview()
        with self.assertRaises(AttributeError):
            overview.total = 0

    def test_slots(self):
        overview = _make_backup_overview()
        with self.assertRaises(AttributeError):
            overview.__dict__

    def test_negative_total_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_backup_overview(total=-1)

    def test_negative_successful_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_backup_overview(successful=-1)

    def test_negative_failed_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_backup_overview(failed=-1)

    def test_zero_values_allowed(self):
        overview = BackupOverview(total=0, successful=0, failed=0)
        self.assertEqual(overview.total, 0)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            BackupOverview(total="10", successful=8, failed=2)


# ============================================================================
# RestoreOverview
# ============================================================================

class TestRestoreOverview(unittest.TestCase):
    """恢复概览测试"""

    def test_valid_overview(self):
        overview = _make_restore_overview()
        self.assertEqual(overview.total, 5)
        self.assertEqual(overview.successful, 4)
        self.assertEqual(overview.failed, 1)

    def test_frozen(self):
        overview = _make_restore_overview()
        with self.assertRaises(AttributeError):
            overview.total = 0

    def test_slots(self):
        overview = _make_restore_overview()
        with self.assertRaises(AttributeError):
            overview.__dict__

    def test_negative_total_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_restore_overview(total=-1)

    def test_negative_successful_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_restore_overview(successful=-1)

    def test_negative_failed_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_restore_overview(failed=-1)

    def test_zero_values_allowed(self):
        overview = RestoreOverview(total=0, successful=0, failed=0)
        self.assertEqual(overview.total, 0)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            RestoreOverview(total="5", successful=4, failed=1)


# ============================================================================
# DashboardService Contract
# ============================================================================

class TestDashboardServiceContract(unittest.TestCase):
    """仪表盘服务契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(DashboardService, ABC))

    def test_has_get_overview(self):
        self.assertTrue(hasattr(DashboardService, "get_overview"))

    def test_has_get_runtime_status(self):
        self.assertTrue(hasattr(DashboardService, "get_runtime_status"))

    def test_has_get_backup_status(self):
        self.assertTrue(hasattr(DashboardService, "get_backup_status"))

    def test_has_get_restore_status(self):
        self.assertTrue(hasattr(DashboardService, "get_restore_status"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            DashboardService()

    def test_concrete_subclass(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return [_make_runtime_overview()]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        overview = service.get_overview()
        self.assertEqual(overview.system_name, "WorkOps")

    def test_missing_get_overview(self):
        class BadService(DashboardService):
            def get_runtime_status(self):
                pass
            def get_backup_status(self):
                pass
            def get_restore_status(self):
                pass
        with self.assertRaises(TypeError):
            BadService()

    def test_missing_get_runtime_status(self):
        class BadService(DashboardService):
            def get_overview(self):
                pass
            def get_backup_status(self):
                pass
            def get_restore_status(self):
                pass
        with self.assertRaises(TypeError):
            BadService()


# ============================================================================
# DashboardRoutes Contract
# ============================================================================

class TestDashboardRoutesContract(unittest.TestCase):
    """仪表盘路由契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(DashboardRoutes, ABC))

    def test_has_register_routes(self):
        self.assertTrue(hasattr(DashboardRoutes, "register_routes"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            DashboardRoutes()

    def test_concrete_subclass(self):
        class MockRoutes(DashboardRoutes):
            def __init__(self):
                self.routes = []
            def register_routes(self):
                self.routes = ["/", "/overview", "/runtime", "/backup", "/restore", "/health", "/metrics", "/audit"]
        routes = MockRoutes()
        routes.register_routes()
        self.assertEqual(len(routes.routes), 8)

    def test_missing_register_routes(self):
        class BadRoutes(DashboardRoutes):
            pass
        with self.assertRaises(TypeError):
            BadRoutes()


# ============================================================================
# Error Model
# ============================================================================

class TestDashboardErrors(unittest.TestCase):
    """错误模型测试"""

    def test_dashboard_error(self):
        with self.assertRaises(DashboardError):
            raise DashboardError("test")

    def test_unavailable_error(self):
        with self.assertRaises(DashboardError):
            raise DashboardUnavailableError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(DashboardError):
            raise InvalidDashboardRequestError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (DashboardError, ("test",)),
            (DashboardUnavailableError, ("test",)),
            (InvalidDashboardRequestError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_view_model_no_credentials(self):
        model = _make_view_model()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(model, attr))

    def test_runtime_overview_no_credentials(self):
        overview = _make_runtime_overview()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(overview, attr))

    def test_backup_overview_no_credentials(self):
        overview = _make_backup_overview()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(overview, attr))

    def test_restore_overview_no_credentials(self):
        overview = _make_restore_overview()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(overview, attr))

    def test_no_subprocess(self):
        import ast
        import os
        dash_dir = os.path.join("backup_manager", "dashboard")
        for filename in os.listdir(dash_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dash_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                        self.assertNotEqual(alias.name, "os")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if "subprocess" in node.module:
                            self.fail(f"subprocess imported in {filename}")

    def test_no_exec_eval(self):
        import ast
        import os
        dash_dir = os.path.join("backup_manager", "dashboard")
        for filename in os.listdir(dash_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dash_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_service_lifecycle(self):
        """完整服务生命周期"""
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return [_make_runtime_overview()]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        overview = service.get_overview()
        self.assertEqual(overview.status, DashboardStatus.ONLINE)
        runtimes = service.get_runtime_status()
        self.assertEqual(len(runtimes), 1)
        backup = service.get_backup_status()
        self.assertEqual(backup.total, 10)
        restore = service.get_restore_status()
        self.assertEqual(restore.total, 5)


# ============================================================================
# Extended Tests
# ============================================================================

class TestDashboardExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(DashboardUnavailableError, DashboardError))
        self.assertTrue(issubclass(InvalidDashboardRequestError, DashboardError))

    def test_view_model_preserves_all_fields(self):
        model = _make_view_model()
        self.assertEqual(model.system_name, "WorkOps")
        self.assertEqual(model.status, DashboardStatus.ONLINE)
        self.assertEqual(model.runtime_count, 3)

    def test_runtime_overview_preserves_all_fields(self):
        overview = _make_runtime_overview()
        self.assertEqual(overview.runtime_name, "linux-ssh")
        self.assertTrue(overview.connected)
        self.assertEqual(overview.message, "connected")

    def test_backup_overview_preserves_all_fields(self):
        overview = _make_backup_overview()
        self.assertEqual(overview.total, 10)
        self.assertEqual(overview.successful, 8)
        self.assertEqual(overview.failed, 2)

    def test_restore_overview_preserves_all_fields(self):
        overview = _make_restore_overview()
        self.assertEqual(overview.total, 5)
        self.assertEqual(overview.successful, 4)
        self.assertEqual(overview.failed, 1)

    def test_view_model_repr_no_secrets(self):
        model = _make_view_model()
        r = repr(model)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_runtime_overview_repr_no_secrets(self):
        overview = _make_runtime_overview()
        r = repr(overview)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_view_model_no_password(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "password"))

    def test_view_model_no_secret(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "secret"))

    def test_view_model_no_token(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "token"))

    def test_view_model_no_credential(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "credential"))

    def test_view_model_no_private_key(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "private_key"))

    def test_view_model_whitespace_name_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_view_model(system_name="   ")

    def test_runtime_overview_empty_name_rejected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            _make_runtime_overview(runtime_name="")

    def test_runtime_overview_empty_message_accepted(self):
        overview = _make_runtime_overview(message="")
        self.assertEqual(overview.message, "")

    def test_view_model_different_system_names(self):
        for name in ["WorkOps", "Production", "Staging"]:
            model = _make_view_model(system_name=name)
            self.assertEqual(model.system_name, name)

    def test_view_model_different_runtime_counts(self):
        for count in [0, 1, 5, 100]:
            model = _make_view_model(runtime_count=count)
            self.assertEqual(model.runtime_count, count)

    def test_runtime_overview_different_names(self):
        for name in ["linux-ssh", "pve-api", "omv-api"]:
            overview = _make_runtime_overview(runtime_name=name)
            self.assertEqual(overview.runtime_name, name)

    def test_backup_overview_different_values(self):
        for total in [0, 1, 50, 1000]:
            overview = BackupOverview(total=total, successful=total, failed=0)
            self.assertEqual(overview.total, total)

    def test_restore_overview_different_values(self):
        for total in [0, 1, 50, 1000]:
            overview = RestoreOverview(total=total, successful=total, failed=0)
            self.assertEqual(overview.total, total)

    def test_service_returns_view_model(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return [_make_runtime_overview()]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_overview()
        self.assertIsInstance(result, DashboardViewModel)

    def test_service_returns_runtime_list(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return [_make_runtime_overview(), _make_runtime_overview(runtime_name="pve-api")]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_runtime_status()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_service_returns_backup_overview(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_backup_status()
        self.assertIsInstance(result, BackupOverview)

    def test_service_returns_restore_overview(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_restore_status()
        self.assertIsInstance(result, RestoreOverview)

    def test_routes_register_returns_none(self):
        class MockRoutes(DashboardRoutes):
            def register_routes(self):
                pass
        routes = MockRoutes()
        result = routes.register_routes()
        self.assertIsNone(result)

    def test_error_messages_safe(self):
        try:
            raise DashboardError("test")
        except DashboardError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_unavailable_error_message(self):
        exc = DashboardUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_invalid_request_error_message(self):
        exc = InvalidDashboardRequestError("invalid request")
        self.assertIn("invalid request", str(exc))

    def test_view_model_created_at_type(self):
        from datetime import datetime
        model = _make_view_model()
        self.assertIsInstance(model.created_at, datetime)

    def test_status_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(DashboardStatus, Enum))

    def test_error_hierarchy_deep(self):
        self.assertTrue(issubclass(DashboardError, Exception))
        self.assertTrue(issubclass(DashboardUnavailableError, Exception))
        self.assertTrue(issubclass(InvalidDashboardRequestError, Exception))

    def test_view_model_no_ssh(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "ssh"))

    def test_view_model_no_command(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "command"))

    def test_view_model_no_subprocess(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "subprocess"))

    def test_view_model_no_shell(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "shell"))

    def test_runtime_overview_no_password(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "password"))

    def test_runtime_overview_no_secret(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "secret"))

    def test_runtime_overview_no_token(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "token"))

    def test_runtime_overview_no_private_key(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "private_key"))

    def test_backup_overview_no_password(self):
        overview = _make_backup_overview()
        self.assertFalse(hasattr(overview, "password"))

    def test_backup_overview_no_secret(self):
        overview = _make_backup_overview()
        self.assertFalse(hasattr(overview, "secret"))

    def test_restore_overview_no_password(self):
        overview = _make_restore_overview()
        self.assertFalse(hasattr(overview, "password"))

    def test_restore_overview_no_secret(self):
        overview = _make_restore_overview()
        self.assertFalse(hasattr(overview, "secret"))

    def test_view_model_all_fields_present(self):
        model = _make_view_model()
        self.assertTrue(hasattr(model, "system_name"))
        self.assertTrue(hasattr(model, "status"))
        self.assertTrue(hasattr(model, "runtime_count"))
        self.assertTrue(hasattr(model, "created_at"))

    def test_runtime_overview_all_fields_present(self):
        overview = _make_runtime_overview()
        self.assertTrue(hasattr(overview, "runtime_name"))
        self.assertTrue(hasattr(overview, "connected"))
        self.assertTrue(hasattr(overview, "message"))

    def test_backup_overview_all_fields_present(self):
        overview = _make_backup_overview()
        self.assertTrue(hasattr(overview, "total"))
        self.assertTrue(hasattr(overview, "successful"))
        self.assertTrue(hasattr(overview, "failed"))

    def test_restore_overview_all_fields_present(self):
        overview = _make_restore_overview()
        self.assertTrue(hasattr(overview, "total"))
        self.assertTrue(hasattr(overview, "successful"))
        self.assertTrue(hasattr(overview, "failed"))

    def test_status_online_value(self):
        self.assertEqual(DashboardStatus.ONLINE.value, "online")

    def test_status_degraded_value(self):
        self.assertEqual(DashboardStatus.DEGRADED.value, "degraded")

    def test_status_offline_value(self):
        self.assertEqual(DashboardStatus.OFFLINE.value, "offline")

    def test_backup_overview_invalid_type_successful(self):
        with self.assertRaises(InvalidDashboardRequestError):
            BackupOverview(total=10, successful="8", failed=2)

    def test_backup_overview_invalid_type_failed(self):
        with self.assertRaises(InvalidDashboardRequestError):
            BackupOverview(total=10, successful=8, failed="2")

    def test_restore_overview_invalid_type_successful(self):
        with self.assertRaises(InvalidDashboardRequestError):
            RestoreOverview(total=5, successful="4", failed=1)

    def test_restore_overview_invalid_type_failed(self):
        with self.assertRaises(InvalidDashboardRequestError):
            RestoreOverview(total=5, successful=4, failed="1")

    def test_service_multiple_calls(self):
        class MockService(DashboardService):
            def __init__(self):
                self.call_count = 0
            def get_overview(self):
                self.call_count += 1
                return _make_view_model()
            def get_runtime_status(self):
                self.call_count += 1
                return []
            def get_backup_status(self):
                self.call_count += 1
                return _make_backup_overview()
            def get_restore_status(self):
                self.call_count += 1
                return _make_restore_overview()
            def get_health_status(self):
                self.call_count += 1
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                self.call_count += 1
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                self.call_count += 1
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        service.get_overview()
        service.get_runtime_status()
        service.get_backup_status()
        service.get_restore_status()
        service.get_health_status()
        service.get_metrics_status()
        service.get_audit_status()
        self.assertEqual(service.call_count, 7)

    def test_view_model_large_runtime_count(self):
        model = _make_view_model(runtime_count=1000)
        self.assertEqual(model.runtime_count, 1000)

    def test_backup_overview_large_values(self):
        overview = BackupOverview(total=99999, successful=99999, failed=0)
        self.assertEqual(overview.total, 99999)

    def test_restore_overview_large_values(self):
        overview = RestoreOverview(total=99999, successful=99999, failed=0)
        self.assertEqual(overview.total, 99999)

    def test_runtime_overview_connected_true(self):
        overview = _make_runtime_overview(connected=True)
        self.assertTrue(overview.connected)

    def test_runtime_overview_connected_false(self):
        overview = _make_runtime_overview(connected=False, message="down")
        self.assertFalse(overview.connected)

    def test_view_model_status_degraded(self):
        model = _make_view_model(status=DashboardStatus.DEGRADED)
        self.assertEqual(model.status, DashboardStatus.DEGRADED)

    def test_view_model_status_offline(self):
        model = _make_view_model(status=DashboardStatus.OFFLINE)
        self.assertEqual(model.status, DashboardStatus.OFFLINE)

    def test_routes_all_eight_routes(self):
        class MockRoutes(DashboardRoutes):
            def register_routes(self):
                return ["/", "/overview", "/runtime", "/backup", "/restore", "/health", "/metrics", "/audit"]
        routes = MockRoutes()
        result = routes.register_routes()
        self.assertEqual(len(result), 8)

    def test_service_get_overview_returns_model(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_overview()
        self.assertIsInstance(result, DashboardViewModel)

    def test_service_get_runtime_returns_list(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return [_make_runtime_overview()]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_runtime_status()
        self.assertIsInstance(result, list)

    def test_service_get_backup_returns_overview(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_backup_status()
        self.assertIsInstance(result, BackupOverview)

    def test_service_get_restore_returns_overview(self):
        class MockService(DashboardService):
            def get_overview(self):
                return _make_view_model()
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return HealthSummary(system_state="healthy", runtime_available=True, message="ok")
            def get_metrics_status(self):
                return MetricsSummary(operation_count=100, runtime_count=3, message="ok")
            def get_audit_status(self):
                return AuditSummary(total_events=500, recent_events=10, message="ok")
        service = MockService()
        result = service.get_restore_status()
        self.assertIsInstance(result, RestoreOverview)

    def test_backup_overview_all_zero(self):
        overview = BackupOverview(total=0, successful=0, failed=0)
        self.assertEqual(overview.total, 0)
        self.assertEqual(overview.successful, 0)
        self.assertEqual(overview.failed, 0)

    def test_restore_overview_all_zero(self):
        overview = RestoreOverview(total=0, successful=0, failed=0)
        self.assertEqual(overview.total, 0)
        self.assertEqual(overview.successful, 0)
        self.assertEqual(overview.failed, 0)

    def test_runtime_overview_no_command(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "command"))

    def test_runtime_overview_no_ssh(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "ssh"))

    def test_backup_overview_no_token(self):
        overview = _make_backup_overview()
        self.assertFalse(hasattr(overview, "token"))

    def test_backup_overview_no_credential(self):
        overview = _make_backup_overview()
        self.assertFalse(hasattr(overview, "credential"))

    def test_restore_overview_no_token(self):
        overview = _make_restore_overview()
        self.assertFalse(hasattr(overview, "token"))

    def test_restore_overview_no_credential(self):
        overview = _make_restore_overview()
        self.assertFalse(hasattr(overview, "credential"))

    def test_view_model_no_stdout(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "stdout"))

    def test_view_model_no_stderr(self):
        model = _make_view_model()
        self.assertFalse(hasattr(model, "stderr"))

    def test_runtime_overview_no_stdout(self):
        overview = _make_runtime_overview()
        self.assertFalse(hasattr(overview, "stdout"))

    def test_backup_overview_no_private_key(self):
        overview = _make_backup_overview()
        self.assertFalse(hasattr(overview, "private_key"))

    def test_restore_overview_no_private_key(self):
        overview = _make_restore_overview()
        self.assertFalse(hasattr(overview, "private_key"))

    def test_dashboard_status_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(DashboardStatus, Enum))

    def test_view_model_invalid_type_system_name(self):
        with self.assertRaises(InvalidDashboardRequestError):
            DashboardViewModel(system_name=123, status=DashboardStatus.ONLINE, runtime_count=3)

    def test_view_model_invalid_type_runtime_count(self):
        with self.assertRaises(InvalidDashboardRequestError):
            DashboardViewModel(system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count="3")

    def test_runtime_overview_invalid_type_runtime_name(self):
        with self.assertRaises(InvalidDashboardRequestError):
            RuntimeOverview(runtime_name=123, connected=True, message="ok")

    def test_runtime_overview_invalid_type_connected(self):
        with self.assertRaises(InvalidDashboardRequestError):
            RuntimeOverview(runtime_name="linux", connected=1, message="ok")


if __name__ == "__main__":
    unittest.main()
