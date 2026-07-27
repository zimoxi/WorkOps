"""
WorkOps Dashboard Runtime Integration Tests
Sprint075: Dashboard Runtime Integration

覆盖：
- RuntimeDashboardProvider contract
- BackupDashboardProvider contract
- RestoreDashboardProvider contract
- HealthDashboardProvider contract
- MetricsDashboardProvider contract
- AuditDashboardProvider contract
- DashboardService integration
- DashboardRoutes integration
- HealthSummary model
- MetricsSummary model
- AuditSummary model
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
from backup_manager.dashboard.providers import (
    RuntimeDashboardProvider,
    BackupDashboardProvider,
    RestoreDashboardProvider,
    HealthDashboardProvider,
    MetricsDashboardProvider,
    AuditDashboardProvider,
)
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

def _make_runtime_overview(**kwargs):
    defaults = {"runtime_name": "linux-ssh", "connected": True, "message": "ok"}
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


def _make_health_summary(**kwargs):
    defaults = {"system_state": "healthy", "runtime_available": True, "message": "all systems operational"}
    defaults.update(kwargs)
    return HealthSummary(**defaults)


def _make_metrics_summary(**kwargs):
    defaults = {"operation_count": 100, "runtime_count": 3, "message": "normal"}
    defaults.update(kwargs)
    return MetricsSummary(**defaults)


def _make_audit_summary(**kwargs):
    defaults = {"total_events": 500, "recent_events": 10, "message": "no issues"}
    defaults.update(kwargs)
    return AuditSummary(**defaults)


# ============================================================================
# HealthSummary
# ============================================================================

class TestHealthSummary(unittest.TestCase):
    """健康摘要测试"""

    def test_valid_summary(self):
        summary = _make_health_summary()
        self.assertEqual(summary.system_state, "healthy")
        self.assertTrue(summary.runtime_available)
        self.assertEqual(summary.message, "all systems operational")

    def test_frozen(self):
        summary = _make_health_summary()
        with self.assertRaises(AttributeError):
            summary.system_state = "other"

    def test_slots(self):
        summary = _make_health_summary()
        with self.assertRaises(AttributeError):
            summary.__dict__

    def test_unhealthy(self):
        summary = _make_health_summary(system_state="unhealthy", runtime_available=False, message="degraded")
        self.assertFalse(summary.runtime_available)

    def test_no_forbidden_fields(self):
        summary = _make_health_summary()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(summary, attr))


# ============================================================================
# MetricsSummary
# ============================================================================

class TestMetricsSummary(unittest.TestCase):
    """指标摘要测试"""

    def test_valid_summary(self):
        summary = _make_metrics_summary()
        self.assertEqual(summary.operation_count, 100)
        self.assertEqual(summary.runtime_count, 3)

    def test_frozen(self):
        summary = _make_metrics_summary()
        with self.assertRaises(AttributeError):
            summary.operation_count = 0

    def test_slots(self):
        summary = _make_metrics_summary()
        with self.assertRaises(AttributeError):
            summary.__dict__

    def test_zero_values(self):
        summary = MetricsSummary(operation_count=0, runtime_count=0, message="empty")
        self.assertEqual(summary.operation_count, 0)

    def test_no_forbidden_fields(self):
        summary = _make_metrics_summary()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(summary, attr))


# ============================================================================
# AuditSummary
# ============================================================================

class TestAuditSummary(unittest.TestCase):
    """审计摘要测试"""

    def test_valid_summary(self):
        summary = _make_audit_summary()
        self.assertEqual(summary.total_events, 500)
        self.assertEqual(summary.recent_events, 10)

    def test_frozen(self):
        summary = _make_audit_summary()
        with self.assertRaises(AttributeError):
            summary.total_events = 0

    def test_slots(self):
        summary = _make_audit_summary()
        with self.assertRaises(AttributeError):
            summary.__dict__

    def test_zero_values(self):
        summary = AuditSummary(total_events=0, recent_events=0, message="empty")
        self.assertEqual(summary.total_events, 0)

    def test_no_forbidden_fields(self):
        summary = _make_audit_summary()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(summary, attr))


# ============================================================================
# RuntimeDashboardProvider Contract
# ============================================================================

class TestRuntimeDashboardProviderContract(unittest.TestCase):
    """运行时仪表盘数据提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RuntimeDashboardProvider, ABC))

    def test_has_get_runtime_overview(self):
        self.assertTrue(hasattr(RuntimeDashboardProvider, "get_runtime_overview"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RuntimeDashboardProvider()

    def test_concrete_subclass(self):
        class MockProvider(RuntimeDashboardProvider):
            def get_runtime_overview(self):
                return [_make_runtime_overview()]
        provider = MockProvider()
        result = provider.get_runtime_overview()
        self.assertEqual(len(result), 1)

    def test_missing_method(self):
        class BadProvider(RuntimeDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# BackupDashboardProvider Contract
# ============================================================================

class TestBackupDashboardProviderContract(unittest.TestCase):
    """备份仪表盘数据提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(BackupDashboardProvider, ABC))

    def test_has_get_backup_overview(self):
        self.assertTrue(hasattr(BackupDashboardProvider, "get_backup_overview"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            BackupDashboardProvider()

    def test_concrete_subclass(self):
        class MockProvider(BackupDashboardProvider):
            def get_backup_overview(self):
                return _make_backup_overview()
        provider = MockProvider()
        result = provider.get_backup_overview()
        self.assertEqual(result.total, 10)


# ============================================================================
# RestoreDashboardProvider Contract
# ============================================================================

class TestRestoreDashboardProviderContract(unittest.TestCase):
    """恢复仪表盘数据提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreDashboardProvider, ABC))

    def test_has_get_restore_overview(self):
        self.assertTrue(hasattr(RestoreDashboardProvider, "get_restore_overview"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreDashboardProvider()

    def test_concrete_subclass(self):
        class MockProvider(RestoreDashboardProvider):
            def get_restore_overview(self):
                return _make_restore_overview()
        provider = MockProvider()
        result = provider.get_restore_overview()
        self.assertEqual(result.total, 5)


# ============================================================================
# HealthDashboardProvider Contract
# ============================================================================

class TestHealthDashboardProviderContract(unittest.TestCase):
    """健康仪表盘数据提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(HealthDashboardProvider, ABC))

    def test_has_get_health_summary(self):
        self.assertTrue(hasattr(HealthDashboardProvider, "get_health_summary"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            HealthDashboardProvider()

    def test_concrete_subclass(self):
        class MockProvider(HealthDashboardProvider):
            def get_health_summary(self):
                return _make_health_summary()
        provider = MockProvider()
        result = provider.get_health_summary()
        self.assertEqual(result.system_state, "healthy")


# ============================================================================
# MetricsDashboardProvider Contract
# ============================================================================

class TestMetricsDashboardProviderContract(unittest.TestCase):
    """指标仪表盘数据提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(MetricsDashboardProvider, ABC))

    def test_has_get_metrics_summary(self):
        self.assertTrue(hasattr(MetricsDashboardProvider, "get_metrics_summary"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            MetricsDashboardProvider()

    def test_concrete_subclass(self):
        class MockProvider(MetricsDashboardProvider):
            def get_metrics_summary(self):
                return _make_metrics_summary()
        provider = MockProvider()
        result = provider.get_metrics_summary()
        self.assertEqual(result.operation_count, 100)


# ============================================================================
# AuditDashboardProvider Contract
# ============================================================================

class TestAuditDashboardProviderContract(unittest.TestCase):
    """审计仪表盘数据提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AuditDashboardProvider, ABC))

    def test_has_get_audit_summary(self):
        self.assertTrue(hasattr(AuditDashboardProvider, "get_audit_summary"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AuditDashboardProvider()

    def test_concrete_subclass(self):
        class MockProvider(AuditDashboardProvider):
            def get_audit_summary(self):
                return _make_audit_summary()
        provider = MockProvider()
        result = provider.get_audit_summary()
        self.assertEqual(result.total_events, 500)


# ============================================================================
# DashboardService Integration
# ============================================================================

class TestDashboardServiceIntegration(unittest.TestCase):
    """仪表盘服务集成测试"""

    def _make_service(self):
        class MockService(DashboardService):
            def get_overview(self):
                return DashboardViewModel(
                    system_name="WorkOps",
                    status=DashboardStatus.ONLINE,
                    runtime_count=3,
                )
            def get_runtime_status(self):
                return [
                    _make_runtime_overview(),
                    _make_runtime_overview(runtime_name="pve-api", connected=True, message="ok"),
                    _make_runtime_overview(runtime_name="omv-api", connected=True, message="ok"),
                ]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return _make_health_summary()
            def get_metrics_status(self):
                return _make_metrics_summary()
            def get_audit_status(self):
                return _make_audit_summary()
        return MockService()

    def test_get_overview(self):
        service = self._make_service()
        result = service.get_overview()
        self.assertEqual(result.system_name, "WorkOps")
        self.assertEqual(result.status, DashboardStatus.ONLINE)

    def test_get_runtime_status(self):
        service = self._make_service()
        result = service.get_runtime_status()
        self.assertEqual(len(result), 3)

    def test_get_backup_status(self):
        service = self._make_service()
        result = service.get_backup_status()
        self.assertEqual(result.total, 10)

    def test_get_restore_status(self):
        service = self._make_service()
        result = service.get_restore_status()
        self.assertEqual(result.total, 5)

    def test_get_health_status(self):
        service = self._make_service()
        result = service.get_health_status()
        self.assertEqual(result.system_state, "healthy")

    def test_get_metrics_status(self):
        service = self._make_service()
        result = service.get_metrics_status()
        self.assertEqual(result.operation_count, 100)

    def test_get_audit_status(self):
        service = self._make_service()
        result = service.get_audit_status()
        self.assertEqual(result.total_events, 500)

    def test_service_has_all_methods(self):
        self.assertTrue(hasattr(DashboardService, "get_overview"))
        self.assertTrue(hasattr(DashboardService, "get_runtime_status"))
        self.assertTrue(hasattr(DashboardService, "get_backup_status"))
        self.assertTrue(hasattr(DashboardService, "get_restore_status"))
        self.assertTrue(hasattr(DashboardService, "get_health_status"))
        self.assertTrue(hasattr(DashboardService, "get_metrics_status"))
        self.assertTrue(hasattr(DashboardService, "get_audit_status"))

    def test_service_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(DashboardService, ABC))

    def test_service_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            DashboardService()


# ============================================================================
# DashboardRoutes Integration
# ============================================================================

class TestDashboardRoutesIntegration(unittest.TestCase):
    """仪表盘路由集成测试"""

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


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_health_summary_no_credentials(self):
        summary = _make_health_summary()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(summary, attr))

    def test_metrics_summary_no_credentials(self):
        summary = _make_metrics_summary()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(summary, attr))

    def test_audit_summary_no_credentials(self):
        summary = _make_audit_summary()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(summary, attr))

    def test_no_subprocess(self):
        import ast
        import os
        providers_dir = os.path.join("backup_manager", "dashboard", "providers")
        for filename in os.listdir(providers_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(providers_dir, filename)
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
        providers_dir = os.path.join("backup_manager", "dashboard", "providers")
        for filename in os.listdir(providers_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(providers_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_full_lifecycle(self):
        """完整仪表盘服务生命周期"""
        class MockService(DashboardService):
            def get_overview(self):
                return DashboardViewModel(
                    system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count=3,
                )
            def get_runtime_status(self):
                return [_make_runtime_overview()]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return _make_health_summary()
            def get_metrics_status(self):
                return _make_metrics_summary()
            def get_audit_status(self):
                return _make_audit_summary()
        service = MockService()
        overview = service.get_overview()
        self.assertEqual(overview.status, DashboardStatus.ONLINE)
        runtimes = service.get_runtime_status()
        self.assertEqual(len(runtimes), 1)
        backup = service.get_backup_status()
        self.assertEqual(backup.total, 10)
        restore = service.get_restore_status()
        self.assertEqual(restore.total, 5)
        health = service.get_health_status()
        self.assertEqual(health.system_state, "healthy")
        metrics = service.get_metrics_status()
        self.assertEqual(metrics.operation_count, 100)
        audit = service.get_audit_status()
        self.assertEqual(audit.total_events, 500)


# ============================================================================
# Extended Tests
# ============================================================================

class TestDashboardRuntimeExtended(unittest.TestCase):
    """扩展测试"""

    def test_health_summary_preserves_fields(self):
        summary = _make_health_summary()
        self.assertEqual(summary.system_state, "healthy")
        self.assertTrue(summary.runtime_available)
        self.assertEqual(summary.message, "all systems operational")

    def test_metrics_summary_preserves_fields(self):
        summary = _make_metrics_summary()
        self.assertEqual(summary.operation_count, 100)
        self.assertEqual(summary.runtime_count, 3)
        self.assertEqual(summary.message, "normal")

    def test_audit_summary_preserves_fields(self):
        summary = _make_audit_summary()
        self.assertEqual(summary.total_events, 500)
        self.assertEqual(summary.recent_events, 10)
        self.assertEqual(summary.message, "no issues")

    def test_health_summary_repr_no_secrets(self):
        summary = _make_health_summary()
        r = repr(summary)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_metrics_summary_repr_no_secrets(self):
        summary = _make_metrics_summary()
        r = repr(summary)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_audit_summary_repr_no_secrets(self):
        summary = _make_audit_summary()
        r = repr(summary)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_health_summary_no_password(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "password"))

    def test_health_summary_no_secret(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "secret"))

    def test_health_summary_no_token(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "token"))

    def test_metrics_summary_no_password(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "password"))

    def test_metrics_summary_no_secret(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "secret"))

    def test_metrics_summary_no_token(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "token"))

    def test_audit_summary_no_password(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "password"))

    def test_audit_summary_no_secret(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "secret"))

    def test_audit_summary_no_token(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "token"))

    def test_health_summary_no_private_key(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "private_key"))

    def test_metrics_summary_no_private_key(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "private_key"))

    def test_audit_summary_no_private_key(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "private_key"))

    def test_provider_runtime_returns_list(self):
        class MockProvider(RuntimeDashboardProvider):
            def get_runtime_overview(self):
                return [_make_runtime_overview(), _make_runtime_overview(runtime_name="pve-api")]
        provider = MockProvider()
        result = provider.get_runtime_overview()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_provider_backup_returns_overview(self):
        class MockProvider(BackupDashboardProvider):
            def get_backup_overview(self):
                return _make_backup_overview()
        provider = MockProvider()
        result = provider.get_backup_overview()
        self.assertIsInstance(result, BackupOverview)

    def test_provider_restore_returns_overview(self):
        class MockProvider(RestoreDashboardProvider):
            def get_restore_overview(self):
                return _make_restore_overview()
        provider = MockProvider()
        result = provider.get_restore_overview()
        self.assertIsInstance(result, RestoreOverview)

    def test_provider_health_returns_summary(self):
        class MockProvider(HealthDashboardProvider):
            def get_health_summary(self):
                return _make_health_summary()
        provider = MockProvider()
        result = provider.get_health_summary()
        self.assertIsInstance(result, HealthSummary)

    def test_provider_metrics_returns_summary(self):
        class MockProvider(MetricsDashboardProvider):
            def get_metrics_summary(self):
                return _make_metrics_summary()
        provider = MockProvider()
        result = provider.get_metrics_summary()
        self.assertIsInstance(result, MetricsSummary)

    def test_provider_audit_returns_summary(self):
        class MockProvider(AuditDashboardProvider):
            def get_audit_summary(self):
                return _make_audit_summary()
        provider = MockProvider()
        result = provider.get_audit_summary()
        self.assertIsInstance(result, AuditSummary)

    def test_service_all_methods_return_correct_types(self):
        class MockService(DashboardService):
            def get_overview(self):
                return DashboardViewModel(system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count=3)
            def get_runtime_status(self):
                return [_make_runtime_overview()]
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return _make_health_summary()
            def get_metrics_status(self):
                return _make_metrics_summary()
            def get_audit_status(self):
                return _make_audit_summary()
        service = MockService()
        self.assertIsInstance(service.get_overview(), DashboardViewModel)
        self.assertIsInstance(service.get_runtime_status(), list)
        self.assertIsInstance(service.get_backup_status(), BackupOverview)
        self.assertIsInstance(service.get_restore_status(), RestoreOverview)
        self.assertIsInstance(service.get_health_status(), HealthSummary)
        self.assertIsInstance(service.get_metrics_status(), MetricsSummary)
        self.assertIsInstance(service.get_audit_status(), AuditSummary)

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(DashboardUnavailableError, DashboardError))
        self.assertTrue(issubclass(InvalidDashboardRequestError, DashboardError))

    def test_error_messages_safe(self):
        try:
            raise DashboardError("test")
        except DashboardError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())

    def test_health_summary_all_fields_present(self):
        summary = _make_health_summary()
        self.assertTrue(hasattr(summary, "system_state"))
        self.assertTrue(hasattr(summary, "runtime_available"))
        self.assertTrue(hasattr(summary, "message"))

    def test_metrics_summary_all_fields_present(self):
        summary = _make_metrics_summary()
        self.assertTrue(hasattr(summary, "operation_count"))
        self.assertTrue(hasattr(summary, "runtime_count"))
        self.assertTrue(hasattr(summary, "message"))

    def test_audit_summary_all_fields_present(self):
        summary = _make_audit_summary()
        self.assertTrue(hasattr(summary, "total_events"))
        self.assertTrue(hasattr(summary, "recent_events"))
        self.assertTrue(hasattr(summary, "message"))

    def test_health_summary_is_frozen_dataclass(self):
        summary = _make_health_summary()
        self.assertTrue(hasattr(summary, '__dataclass_params__'))
        self.assertTrue(summary.__dataclass_params__.frozen)

    def test_metrics_summary_is_frozen_dataclass(self):
        summary = _make_metrics_summary()
        self.assertTrue(hasattr(summary, '__dataclass_params__'))
        self.assertTrue(summary.__dataclass_params__.frozen)

    def test_audit_summary_is_frozen_dataclass(self):
        summary = _make_audit_summary()
        self.assertTrue(hasattr(summary, '__dataclass_params__'))
        self.assertTrue(summary.__dataclass_params__.frozen)

    def test_health_summary_no_ssh(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "ssh"))

    def test_health_summary_no_command(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "command"))

    def test_metrics_summary_no_ssh(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "ssh"))

    def test_audit_summary_no_ssh(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "ssh"))

    def test_health_summary_no_subprocess(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "subprocess"))

    def test_health_summary_no_shell(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "shell"))

    def test_metrics_summary_no_subprocess(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "subprocess"))

    def test_metrics_summary_no_shell(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "shell"))

    def test_audit_summary_no_subprocess(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "subprocess"))

    def test_audit_summary_no_shell(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "shell"))

    def test_health_summary_no_stdout(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "stdout"))

    def test_metrics_summary_no_stdout(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "stdout"))

    def test_audit_summary_no_stdout(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "stdout"))

    def test_health_summary_no_stderr(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "stderr"))

    def test_metrics_summary_no_stderr(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "stderr"))

    def test_audit_summary_no_stderr(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "stderr"))

    def test_health_summary_no_credential(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "credential"))

    def test_metrics_summary_no_credential(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "credential"))

    def test_audit_summary_no_credential(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "credential"))

    def test_health_summary_no_command(self):
        summary = _make_health_summary()
        self.assertFalse(hasattr(summary, "command"))

    def test_metrics_summary_no_command(self):
        summary = _make_metrics_summary()
        self.assertFalse(hasattr(summary, "command"))

    def test_audit_summary_no_command(self):
        summary = _make_audit_summary()
        self.assertFalse(hasattr(summary, "command"))

    def test_provider_runtime_empty_list(self):
        class MockProvider(RuntimeDashboardProvider):
            def get_runtime_overview(self):
                return []
        provider = MockProvider()
        result = provider.get_runtime_overview()
        self.assertEqual(len(result), 0)

    def test_provider_runtime_multiple(self):
        class MockProvider(RuntimeDashboardProvider):
            def get_runtime_overview(self):
                return [
                    _make_runtime_overview(),
                    _make_runtime_overview(runtime_name="pve-api"),
                    _make_runtime_overview(runtime_name="omv-api"),
                ]
        provider = MockProvider()
        result = provider.get_runtime_overview()
        self.assertEqual(len(result), 3)

    def test_service_missing_get_health_status(self):
        class BadService(DashboardService):
            def get_overview(self):
                pass
            def get_runtime_status(self):
                pass
            def get_backup_status(self):
                pass
            def get_restore_status(self):
                pass
            def get_metrics_status(self):
                pass
            def get_audit_status(self):
                pass
        with self.assertRaises(TypeError):
            BadService()

    def test_service_missing_get_metrics_status(self):
        class BadService(DashboardService):
            def get_overview(self):
                pass
            def get_runtime_status(self):
                pass
            def get_backup_status(self):
                pass
            def get_restore_status(self):
                pass
            def get_health_status(self):
                pass
            def get_audit_status(self):
                pass
        with self.assertRaises(TypeError):
            BadService()

    def test_service_missing_get_audit_status(self):
        class BadService(DashboardService):
            def get_overview(self):
                pass
            def get_runtime_status(self):
                pass
            def get_backup_status(self):
                pass
            def get_restore_status(self):
                pass
            def get_health_status(self):
                pass
            def get_metrics_status(self):
                pass
        with self.assertRaises(TypeError):
            BadService()

    def test_health_summary_different_states(self):
        for state in ["healthy", "unhealthy", "degraded", "unknown"]:
            summary = _make_health_summary(system_state=state)
            self.assertEqual(summary.system_state, state)

    def test_metrics_summary_different_counts(self):
        for count in [0, 1, 100, 10000]:
            summary = MetricsSummary(operation_count=count, runtime_count=3, message="ok")
            self.assertEqual(summary.operation_count, count)

    def test_audit_summary_different_counts(self):
        for count in [0, 1, 500, 10000]:
            summary = AuditSummary(total_events=count, recent_events=10, message="ok")
            self.assertEqual(summary.total_events, count)

    def test_health_summary_runtime_available_true(self):
        summary = _make_health_summary(runtime_available=True)
        self.assertTrue(summary.runtime_available)

    def test_health_summary_runtime_available_false(self):
        summary = _make_health_summary(runtime_available=False, message="down")
        self.assertFalse(summary.runtime_available)

    def test_service_returns_health_summary_type(self):
        class MockService(DashboardService):
            def get_overview(self):
                return DashboardViewModel(system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count=3)
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return _make_health_summary()
            def get_metrics_status(self):
                return _make_metrics_summary()
            def get_audit_status(self):
                return _make_audit_summary()
        service = MockService()
        result = service.get_health_status()
        self.assertIsInstance(result, HealthSummary)

    def test_service_returns_metrics_summary_type(self):
        class MockService(DashboardService):
            def get_overview(self):
                return DashboardViewModel(system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count=3)
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return _make_health_summary()
            def get_metrics_status(self):
                return _make_metrics_summary()
            def get_audit_status(self):
                return _make_audit_summary()
        service = MockService()
        result = service.get_metrics_status()
        self.assertIsInstance(result, MetricsSummary)

    def test_service_returns_audit_summary_type(self):
        class MockService(DashboardService):
            def get_overview(self):
                return DashboardViewModel(system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count=3)
            def get_runtime_status(self):
                return []
            def get_backup_status(self):
                return _make_backup_overview()
            def get_restore_status(self):
                return _make_restore_overview()
            def get_health_status(self):
                return _make_health_summary()
            def get_metrics_status(self):
                return _make_metrics_summary()
            def get_audit_status(self):
                return _make_audit_summary()
        service = MockService()
        result = service.get_audit_status()
        self.assertIsInstance(result, AuditSummary)

    def test_provider_missing_runtime_method(self):
        class BadProvider(RuntimeDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()

    def test_provider_missing_backup_method(self):
        class BadProvider(BackupDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()

    def test_provider_missing_restore_method(self):
        class BadProvider(RestoreDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()

    def test_provider_missing_health_method(self):
        class BadProvider(HealthDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()

    def test_provider_missing_metrics_method(self):
        class BadProvider(MetricsDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()

    def test_provider_missing_audit_method(self):
        class BadProvider(AuditDashboardProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()

    def test_routes_register_returns_none(self):
        class MockRoutes(DashboardRoutes):
            def register_routes(self):
                pass
        routes = MockRoutes()
        result = routes.register_routes()
        self.assertIsNone(result)

    def test_routes_all_eight_routes(self):
        class MockRoutes(DashboardRoutes):
            def register_routes(self):
                return ["/", "/overview", "/runtime", "/backup", "/restore", "/health", "/metrics", "/audit"]
        routes = MockRoutes()
        result = routes.register_routes()
        self.assertEqual(len(result), 8)

    def test_service_multiple_calls(self):
        class MockService(DashboardService):
            def __init__(self):
                self.call_count = 0
            def get_overview(self):
                self.call_count += 1
                return DashboardViewModel(system_name="WorkOps", status=DashboardStatus.ONLINE, runtime_count=3)
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
                return _make_health_summary()
            def get_metrics_status(self):
                self.call_count += 1
                return _make_metrics_summary()
            def get_audit_status(self):
                self.call_count += 1
                return _make_audit_summary()
        service = MockService()
        service.get_overview()
        service.get_runtime_status()
        service.get_backup_status()
        service.get_restore_status()
        service.get_health_status()
        service.get_metrics_status()
        service.get_audit_status()
        self.assertEqual(service.call_count, 7)

    def test_health_summary_message_not_empty(self):
        summary = _make_health_summary()
        self.assertTrue(len(summary.message) > 0)

    def test_metrics_summary_message_not_empty(self):
        summary = _make_metrics_summary()
        self.assertTrue(len(summary.message) > 0)

    def test_audit_summary_message_not_empty(self):
        summary = _make_audit_summary()
        self.assertTrue(len(summary.message) > 0)

    def test_health_summary_zero_runtime(self):
        summary = HealthSummary(system_state="healthy", runtime_available=False, message="no runtimes")
        self.assertFalse(summary.runtime_available)

    def test_metrics_summary_zero_ops(self):
        summary = MetricsSummary(operation_count=0, runtime_count=0, message="idle")
        self.assertEqual(summary.operation_count, 0)
        self.assertEqual(summary.runtime_count, 0)

    def test_audit_summary_zero_events(self):
        summary = AuditSummary(total_events=0, recent_events=0, message="clean")
        self.assertEqual(summary.total_events, 0)
        self.assertEqual(summary.recent_events, 0)

    def test_provider_runtime_returns_runtime_overview_list(self):
        class MockProvider(RuntimeDashboardProvider):
            def get_runtime_overview(self):
                return [_make_runtime_overview()]
        provider = MockProvider()
        result = provider.get_runtime_overview()
        self.assertIsInstance(result[0], RuntimeOverview)

    def test_provider_backup_returns_backup_overview(self):
        class MockProvider(BackupDashboardProvider):
            def get_backup_overview(self):
                return _make_backup_overview()
        provider = MockProvider()
        result = provider.get_backup_overview()
        self.assertIsInstance(result, BackupOverview)

    def test_provider_restore_returns_restore_overview(self):
        class MockProvider(RestoreDashboardProvider):
            def get_restore_overview(self):
                return _make_restore_overview()
        provider = MockProvider()
        result = provider.get_restore_overview()
        self.assertIsInstance(result, RestoreOverview)

    def test_provider_health_returns_health_summary(self):
        class MockProvider(HealthDashboardProvider):
            def get_health_summary(self):
                return _make_health_summary()
        provider = MockProvider()
        result = provider.get_health_summary()
        self.assertIsInstance(result, HealthSummary)

    def test_provider_metrics_returns_metrics_summary(self):
        class MockProvider(MetricsDashboardProvider):
            def get_metrics_summary(self):
                return _make_metrics_summary()
        provider = MockProvider()
        result = provider.get_metrics_summary()
        self.assertIsInstance(result, MetricsSummary)

    def test_provider_audit_returns_audit_summary(self):
        class MockProvider(AuditDashboardProvider):
            def get_audit_summary(self):
                return _make_audit_summary()
        provider = MockProvider()
        result = provider.get_audit_summary()
        self.assertIsInstance(result, AuditSummary)

    def test_dashboard_status_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(DashboardStatus, Enum))

    def test_runtime_overview_is_frozen_dataclass(self):
        overview = _make_runtime_overview()
        self.assertTrue(hasattr(overview, '__dataclass_params__'))
        self.assertTrue(overview.__dataclass_params__.frozen)


if __name__ == "__main__":
    unittest.main()
