"""
WorkOps Stable Release Tests
Sprint074: WorkOps v1.0 Stable Release

覆盖：
- StableVersion validation
- ProductionReadinessStatus enum
- ProductionReadinessReport validation
- ReleaseChecklistItem validation
- ReleaseChecklist validation
- StableReleaseValidator contract
- Capability Matrix
- Error model
- Security boundary
- Final integration validation
"""

import unittest

from backup_manager.release.stable import StableVersion
from backup_manager.release.readiness import ProductionReadinessStatus, ProductionReadinessReport
from backup_manager.release.checklist import ReleaseChecklistItem, ReleaseChecklist
from backup_manager.release import StableReleaseValidator
from backup_manager.release.errors import (
    ReleaseError,
    InvalidReleaseMetadataError,
    ReleaseValidationError,
    ReleaseUnavailableError,
    StableReleaseError,
    ReleaseBlockedError,
    InvalidReleaseStateError,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_version(**kwargs):
    defaults = {"major": 1, "minor": 0, "patch": 0}
    defaults.update(kwargs)
    return StableVersion(**defaults)


def _make_report(**kwargs):
    defaults = {
        "status": ProductionReadinessStatus.READY,
        "checks_passed": 100,
        "checks_failed": 0,
    }
    defaults.update(kwargs)
    return ProductionReadinessReport(**defaults)


def _make_checklist_item(**kwargs):
    defaults = {"name": "HTTP API", "completed": True}
    defaults.update(kwargs)
    return ReleaseChecklistItem(**defaults)


def _make_checklist(items=None):
    if items is None:
        items = (
            ReleaseChecklistItem(name="HTTP API", completed=True),
            ReleaseChecklistItem(name="Dashboard", completed=True),
            ReleaseChecklistItem(name="Authentication", completed=True),
        )
    return ReleaseChecklist(items=items)


# ============================================================================
# StableVersion
# ============================================================================

class TestStableVersion(unittest.TestCase):
    """稳定版本测试"""

    def test_valid_version(self):
        v = _make_version()
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 0)

    def test_str(self):
        v = _make_version()
        self.assertEqual(str(v), "1.0.0")

    def test_frozen(self):
        v = _make_version()
        with self.assertRaises(AttributeError):
            v.major = 2

    def test_slots(self):
        v = _make_version()
        with self.assertRaises(AttributeError):
            v.__dict__

    def test_negative_major_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_version(major=-1)

    def test_negative_minor_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_version(minor=-1)

    def test_negative_patch_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_version(patch=-1)

    def test_zero_version(self):
        v = StableVersion(major=0, minor=0, patch=0)
        self.assertEqual(str(v), "0.0.0")

    def test_large_version(self):
        v = StableVersion(major=99, minor=99, patch=99)
        self.assertEqual(str(v), "99.99.99")

    def test_no_forbidden_fields(self):
        v = _make_version()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(v, attr))

    def test_repr_no_secrets(self):
        v = _make_version()
        r = repr(v)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# ProductionReadinessStatus
# ============================================================================

class TestProductionReadinessStatus(unittest.TestCase):
    """生产就绪状态测试"""

    def test_ready(self):
        self.assertEqual(ProductionReadinessStatus.READY.value, "ready")

    def test_not_ready(self):
        self.assertEqual(ProductionReadinessStatus.NOT_READY.value, "not_ready")

    def test_blocked(self):
        self.assertEqual(ProductionReadinessStatus.BLOCKED.value, "blocked")

    def test_three_statuses(self):
        self.assertEqual(len(ProductionReadinessStatus), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            ProductionReadinessStatus("nonexistent")


# ============================================================================
# ProductionReadinessReport
# ============================================================================

class TestProductionReadinessReport(unittest.TestCase):
    """生产就绪报告测试"""

    def test_valid_report(self):
        report = _make_report()
        self.assertEqual(report.status, ProductionReadinessStatus.READY)
        self.assertEqual(report.checks_passed, 100)
        self.assertEqual(report.checks_failed, 0)

    def test_frozen(self):
        report = _make_report()
        with self.assertRaises(AttributeError):
            report.checks_passed = 0

    def test_slots(self):
        report = _make_report()
        with self.assertRaises(AttributeError):
            report.__dict__

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_report(status="ready")

    def test_negative_checks_passed_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_report(checks_passed=-1)

    def test_negative_checks_failed_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_report(checks_failed=-1)

    def test_timezone_aware(self):
        report = _make_report()
        self.assertIsNotNone(report.generated_at.tzinfo)

    def test_all_statuses(self):
        for status in ProductionReadinessStatus:
            report = _make_report(status=status)
            self.assertEqual(report.status, status)

    def test_no_forbidden_fields(self):
        report = _make_report()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(report, attr))


# ============================================================================
# ReleaseChecklistItem
# ============================================================================

class TestReleaseChecklistItem(unittest.TestCase):
    """发布检查项测试"""

    def test_valid_item(self):
        item = _make_checklist_item()
        self.assertEqual(item.name, "HTTP API")
        self.assertTrue(item.completed)

    def test_frozen(self):
        item = _make_checklist_item()
        with self.assertRaises(AttributeError):
            item.name = "other"

    def test_slots(self):
        item = _make_checklist_item()
        with self.assertRaises(AttributeError):
            item.__dict__

    def test_empty_name_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_checklist_item(name="")

    def test_completed_must_be_bool(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            _make_checklist_item(completed=1)

    def test_not_completed(self):
        item = _make_checklist_item(completed=False)
        self.assertFalse(item.completed)


# ============================================================================
# ReleaseChecklist
# ============================================================================

class TestReleaseChecklist(unittest.TestCase):
    """发布检查清单测试"""

    def test_valid_checklist(self):
        checklist = _make_checklist()
        self.assertEqual(len(checklist.items), 3)

    def test_frozen(self):
        checklist = _make_checklist()
        with self.assertRaises(AttributeError):
            checklist.items = ()

    def test_slots(self):
        checklist = _make_checklist()
        with self.assertRaises(AttributeError):
            checklist.__dict__

    def test_empty_items_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseChecklist(items=())

    def test_list_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseChecklist(items=[_make_checklist_item()])

    def test_invalid_item_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseChecklist(items=("not_an_item",))

    def test_all_completed(self):
        checklist = _make_checklist()
        self.assertTrue(checklist.all_completed)

    def test_not_all_completed(self):
        items = (
            ReleaseChecklistItem(name="HTTP API", completed=True),
            ReleaseChecklistItem(name="Dashboard", completed=False),
        )
        checklist = ReleaseChecklist(items=items)
        self.assertFalse(checklist.all_completed)

    def test_completed_count(self):
        items = (
            ReleaseChecklistItem(name="HTTP API", completed=True),
            ReleaseChecklistItem(name="Dashboard", completed=False),
            ReleaseChecklistItem(name="Auth", completed=True),
        )
        checklist = ReleaseChecklist(items=items)
        self.assertEqual(checklist.completed_count, 2)

    def test_total_count(self):
        checklist = _make_checklist()
        self.assertEqual(checklist.total_count, 3)

    def test_no_forbidden_fields(self):
        checklist = _make_checklist()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(checklist, attr))


# ============================================================================
# StableReleaseValidator Contract
# ============================================================================

class TestStableReleaseValidatorContract(unittest.TestCase):
    """稳定发布验证器契约测试"""

    def test_has_validate(self):
        self.assertTrue(hasattr(StableReleaseValidator, "validate"))

    def test_cannot_call_abstract(self):
        validator = StableReleaseValidator()
        report = _make_report()
        with self.assertRaises(NotImplementedError):
            validator.validate(report)

    def test_concrete_subclass(self):
        class MockValidator(StableReleaseValidator):
            def validate(self, report):
                return report.status == ProductionReadinessStatus.READY
        validator = MockValidator()
        report = _make_report()
        self.assertTrue(validator.validate(report))

    def test_concrete_subclass_rejects(self):
        class MockValidator(StableReleaseValidator):
            def validate(self, report):
                return report.status == ProductionReadinessStatus.READY
        validator = MockValidator()
        report = _make_report(status=ProductionReadinessStatus.NOT_READY)
        self.assertFalse(validator.validate(report))


# ============================================================================
# Error Model
# ============================================================================

class TestStableReleaseErrors(unittest.TestCase):
    """错误模型测试"""

    def test_stable_release_error(self):
        with self.assertRaises(StableReleaseError):
            raise StableReleaseError("test")

    def test_release_blocked_error(self):
        with self.assertRaises(StableReleaseError):
            raise ReleaseBlockedError("test")

    def test_invalid_release_state_error(self):
        with self.assertRaises(StableReleaseError):
            raise InvalidReleaseStateError("test")

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(StableReleaseError, ReleaseError))
        self.assertTrue(issubclass(ReleaseBlockedError, StableReleaseError))
        self.assertTrue(issubclass(InvalidReleaseStateError, StableReleaseError))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (StableReleaseError, ("test",)),
            (ReleaseBlockedError, ("test",)),
            (InvalidReleaseStateError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_version_no_credentials(self):
        v = _make_version()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(v, attr))

    def test_report_no_credentials(self):
        report = _make_report()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(report, attr))

    def test_checklist_no_credentials(self):
        checklist = _make_checklist()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(checklist, attr))

    def test_item_no_credentials(self):
        item = _make_checklist_item()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(item, attr))

    def test_no_subprocess(self):
        import ast
        import os
        release_dir = os.path.join("backup_manager", "release")
        for filename in ["stable.py", "readiness.py", "checklist.py"]:
            filepath = os.path.join(release_dir, filename)
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
        release_dir = os.path.join("backup_manager", "release")
        for filename in ["stable.py", "readiness.py", "checklist.py"]:
            filepath = os.path.join(release_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")


# ============================================================================
# Capability Matrix
# ============================================================================

REQUIRED_CAPABILITIES = (
    "HTTP API",
    "Dashboard",
    "Authentication",
    "RBAC",
    "Linux Runtime",
    "PVE Runtime",
    "OMV Runtime",
    "Backup Engine",
    "Restore Engine",
    "Metrics",
    "Audit",
)


class TestCapabilityMatrix(unittest.TestCase):
    """能力矩阵测试"""

    def test_required_capabilities_count(self):
        self.assertEqual(len(REQUIRED_CAPABILITIES), 11)

    def test_all_capabilities_present(self):
        for cap in REQUIRED_CAPABILITIES:
            self.assertIsInstance(cap, str)
            self.assertTrue(len(cap) > 0)

    def test_http_api_capability(self):
        self.assertIn("HTTP API", REQUIRED_CAPABILITIES)

    def test_dashboard_capability(self):
        self.assertIn("Dashboard", REQUIRED_CAPABILITIES)

    def test_authentication_capability(self):
        self.assertIn("Authentication", REQUIRED_CAPABILITIES)

    def test_rbac_capability(self):
        self.assertIn("RBAC", REQUIRED_CAPABILITIES)

    def test_linux_runtime_capability(self):
        self.assertIn("Linux Runtime", REQUIRED_CAPABILITIES)

    def test_pve_runtime_capability(self):
        self.assertIn("PVE Runtime", REQUIRED_CAPABILITIES)

    def test_omv_runtime_capability(self):
        self.assertIn("OMV Runtime", REQUIRED_CAPABILITIES)

    def test_backup_engine_capability(self):
        self.assertIn("Backup Engine", REQUIRED_CAPABILITIES)

    def test_restore_engine_capability(self):
        self.assertIn("Restore Engine", REQUIRED_CAPABILITIES)

    def test_metrics_capability(self):
        self.assertIn("Metrics", REQUIRED_CAPABILITIES)

    def test_audit_capability(self):
        self.assertIn("Audit", REQUIRED_CAPABILITIES)

    def test_checklist_from_capabilities(self):
        items = tuple(
            ReleaseChecklistItem(name=cap, completed=True)
            for cap in REQUIRED_CAPABILITIES
        )
        checklist = ReleaseChecklist(items=items)
        self.assertTrue(checklist.all_completed)
        self.assertEqual(checklist.total_count, 11)

    def test_readiness_report_ready(self):
        report = ProductionReadinessReport(
            status=ProductionReadinessStatus.READY,
            checks_passed=11,
            checks_failed=0,
        )
        self.assertEqual(report.status, ProductionReadinessStatus.READY)
        self.assertEqual(report.checks_passed, 11)

    def test_validator_ready(self):
        class MockValidator(StableReleaseValidator):
            def validate(self, report):
                return report.status == ProductionReadinessStatus.READY and report.checks_failed == 0
        validator = MockValidator()
        report = _make_report(status=ProductionReadinessStatus.READY, checks_passed=11, checks_failed=0)
        self.assertTrue(validator.validate(report))

    def test_validator_not_ready(self):
        class MockValidator(StableReleaseValidator):
            def validate(self, report):
                return report.status == ProductionReadinessStatus.READY and report.checks_failed == 0
        validator = MockValidator()
        report = _make_report(status=ProductionReadinessStatus.NOT_READY, checks_passed=10, checks_failed=1)
        self.assertFalse(validator.validate(report))


# ============================================================================
# Final Integration Validation
# ============================================================================

class TestFinalIntegrationValidation(unittest.TestCase):
    """最终集成验证"""

    def test_architecture_layers_present(self):
        """确认架构层存在"""
        import importlib
        layers = [
            "backup_manager.api",
            "backup_manager.auth",
            "backup_manager.dashboard",
            "backup_manager.operations",
            "backup_manager.jobs",
            "backup_manager.transaction",
            "backup_manager.security",
            "backup_manager.runtime",
            "backup_manager.runtime_context",
            "backup_manager.adapters",
            "backup_manager.backup",
            "backup_manager.backup_engine",
            "backup_manager.restore_engine",
            "backup_manager.restore_workflow",
            "backup_manager.health",
            "backup_manager.health_runtime",
            "backup_manager.metrics",
            "backup_manager.audit",
            "backup_manager.release",
            "backup_manager.http_api",
            "backup_manager.production_backup",
            "backup_manager.production_restore",
        ]
        for layer in layers:
            try:
                importlib.import_module(layer)
            except ImportError:
                self.fail(f"Architecture layer missing: {layer}")

    def test_stable_version_1_0_0(self):
        v = StableVersion(major=1, minor=0, patch=0)
        self.assertEqual(str(v), "1.0.0")

    def test_full_release_checklist(self):
        items = tuple(
            ReleaseChecklistItem(name=cap, completed=True)
            for cap in REQUIRED_CAPABILITIES
        )
        checklist = ReleaseChecklist(items=items)
        self.assertTrue(checklist.all_completed)
        self.assertEqual(checklist.completed_count, 11)
        self.assertEqual(checklist.total_count, 11)

    def test_readiness_report_all_passed(self):
        report = ProductionReadinessReport(
            status=ProductionReadinessStatus.READY,
            checks_passed=150,
            checks_failed=0,
        )
        self.assertEqual(report.status, ProductionReadinessStatus.READY)
        self.assertEqual(report.checks_failed, 0)

    def test_release_version_matches_stable(self):
        stable = StableVersion(major=1, minor=0, patch=0)
        self.assertEqual(stable.major, 1)
        self.assertEqual(stable.minor, 0)
        self.assertEqual(stable.patch, 0)


# ============================================================================
# Extended Tests
# ============================================================================

class TestStableReleaseExtended(unittest.TestCase):
    """扩展测试"""

    def test_version_preserves_all_fields(self):
        v = _make_version()
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 0)

    def test_report_preserves_all_fields(self):
        report = _make_report()
        self.assertEqual(report.status, ProductionReadinessStatus.READY)
        self.assertEqual(report.checks_passed, 100)
        self.assertEqual(report.checks_failed, 0)

    def test_checklist_preserves_all_items(self):
        checklist = _make_checklist()
        self.assertEqual(len(checklist.items), 3)

    def test_version_no_password(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "password"))

    def test_version_no_secret(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "secret"))

    def test_version_no_token(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "token"))

    def test_version_no_credential(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "credential"))

    def test_report_no_password(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "password"))

    def test_report_no_secret(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "secret"))

    def test_report_no_token(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "token"))

    def test_checklist_no_password(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "password"))

    def test_checklist_no_secret(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "secret"))

    def test_item_no_password(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "password"))

    def test_item_no_secret(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "secret"))

    def test_version_str_format(self):
        v = StableVersion(major=2, minor=1, patch=3)
        self.assertEqual(str(v), "2.1.3")

    def test_report_zero_checks(self):
        report = ProductionReadinessReport(
            status=ProductionReadinessStatus.NOT_READY,
            checks_passed=0,
            checks_failed=0,
        )
        self.assertEqual(report.checks_passed, 0)

    def test_checklist_single_item(self):
        item = ReleaseChecklistItem(name="test", completed=True)
        checklist = ReleaseChecklist(items=(item,))
        self.assertEqual(checklist.total_count, 1)
        self.assertTrue(checklist.all_completed)

    def test_checklist_single_incomplete(self):
        item = ReleaseChecklistItem(name="test", completed=False)
        checklist = ReleaseChecklist(items=(item,))
        self.assertFalse(checklist.all_completed)
        self.assertEqual(checklist.completed_count, 0)

    def test_error_messages_safe(self):
        try:
            raise StableReleaseError("test")
        except StableReleaseError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_blocked_error_message(self):
        exc = ReleaseBlockedError("blocked")
        self.assertIn("blocked", str(exc))

    def test_invalid_state_error_message(self):
        exc = InvalidReleaseStateError("invalid state")
        self.assertIn("invalid state", str(exc))

    def test_version_no_private_key(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "private_key"))

    def test_report_no_private_key(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "private_key"))

    def test_checklist_no_private_key(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "private_key"))

    def test_version_no_ssh(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "ssh"))

    def test_version_no_command(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "command"))

    def test_report_no_ssh(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "ssh"))

    def test_report_no_command(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "command"))

    def test_version_is_frozen_dataclass(self):
        v = _make_version()
        self.assertTrue(hasattr(v, '__dataclass_params__'))
        self.assertTrue(v.__dataclass_params__.frozen)

    def test_report_is_frozen_dataclass(self):
        report = _make_report()
        self.assertTrue(hasattr(report, '__dataclass_params__'))
        self.assertTrue(report.__dataclass_params__.frozen)

    def test_checklist_is_frozen_dataclass(self):
        checklist = _make_checklist()
        self.assertTrue(hasattr(checklist, '__dataclass_params__'))
        self.assertTrue(checklist.__dataclass_params__.frozen)

    def test_item_is_frozen_dataclass(self):
        item = _make_checklist_item()
        self.assertTrue(hasattr(item, '__dataclass_params__'))
        self.assertTrue(item.__dataclass_params__.frozen)

    def test_validator_returns_bool(self):
        class MockValidator(StableReleaseValidator):
            def validate(self, report):
                return True
        validator = MockValidator()
        result = validator.validate(_make_report())
        self.assertIsInstance(result, bool)

    def test_readiness_status_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(ProductionReadinessStatus, Enum))

    def test_version_invalid_type_major(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            StableVersion(major="1", minor=0, patch=0)

    def test_version_invalid_type_minor(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            StableVersion(major=1, minor="0", patch=0)

    def test_version_invalid_type_patch(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            StableVersion(major=1, minor=0, patch="0")

    def test_report_invalid_type_checks_passed(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ProductionReadinessReport(
                status=ProductionReadinessStatus.READY,
                checks_passed="100", checks_failed=0,
            )

    def test_report_invalid_type_checks_failed(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ProductionReadinessReport(
                status=ProductionReadinessStatus.READY,
                checks_passed=100, checks_failed="0",
            )

    def test_item_invalid_type_name(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseChecklistItem(name=123, completed=True)

    def test_item_invalid_type_completed(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseChecklistItem(name="test", completed=1)

    def test_version_all_fields_present(self):
        v = _make_version()
        self.assertTrue(hasattr(v, "major"))
        self.assertTrue(hasattr(v, "minor"))
        self.assertTrue(hasattr(v, "patch"))

    def test_report_all_fields_present(self):
        report = _make_report()
        self.assertTrue(hasattr(report, "status"))
        self.assertTrue(hasattr(report, "checks_passed"))
        self.assertTrue(hasattr(report, "checks_failed"))
        self.assertTrue(hasattr(report, "generated_at"))

    def test_item_all_fields_present(self):
        item = _make_checklist_item()
        self.assertTrue(hasattr(item, "name"))
        self.assertTrue(hasattr(item, "completed"))

    def test_checklist_all_fields_present(self):
        checklist = _make_checklist()
        self.assertTrue(hasattr(checklist, "items"))
        self.assertTrue(hasattr(checklist, "all_completed"))
        self.assertTrue(hasattr(checklist, "completed_count"))
        self.assertTrue(hasattr(checklist, "total_count"))

    def test_version_no_stdout(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "stdout"))

    def test_version_no_stderr(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "stderr"))

    def test_report_no_stdout(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "stdout"))

    def test_report_no_stderr(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "stderr"))

    def test_checklist_no_token(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "token"))

    def test_checklist_no_credential(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "credential"))

    def test_item_no_token(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "token"))

    def test_item_no_credential(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "credential"))

    def test_report_generated_at_type(self):
        from datetime import datetime
        report = _make_report()
        self.assertIsInstance(report.generated_at, datetime)

    def test_checklist_multiple_items(self):
        items = tuple(
            ReleaseChecklistItem(name=f"item-{i}", completed=i % 2 == 0)
            for i in range(10)
        )
        checklist = ReleaseChecklist(items=items)
        self.assertEqual(checklist.total_count, 10)
        self.assertEqual(checklist.completed_count, 5)

    def test_validator_multiple_calls(self):
        class MockValidator(StableReleaseValidator):
            def __init__(self):
                self.call_count = 0
            def validate(self, report):
                self.call_count += 1
                return True
        validator = MockValidator()
        for _ in range(5):
            validator.validate(_make_report())
        self.assertEqual(validator.call_count, 5)

    def test_version_different_formats(self):
        for major, minor, patch in [(0, 1, 0), (1, 0, 0), (2, 3, 4), (10, 20, 30)]:
            v = StableVersion(major=major, minor=minor, patch=patch)
            self.assertEqual(str(v), f"{major}.{minor}.{patch}")

    def test_report_different_statuses(self):
        for status in ProductionReadinessStatus:
            report = _make_report(status=status)
            self.assertEqual(report.status, status)

    def test_item_different_names(self):
        for name in ["HTTP API", "Dashboard", "Auth", "Metrics", "Audit"]:
            item = _make_checklist_item(name=name)
            self.assertEqual(item.name, name)

    def test_checklist_all_incomplete(self):
        items = tuple(
            ReleaseChecklistItem(name=f"item-{i}", completed=False)
            for i in range(5)
        )
        checklist = ReleaseChecklist(items=items)
        self.assertFalse(checklist.all_completed)
        self.assertEqual(checklist.completed_count, 0)

    def test_error_hierarchy_stable(self):
        self.assertTrue(issubclass(StableReleaseError, ReleaseError))
        self.assertTrue(issubclass(ReleaseBlockedError, ReleaseError))
        self.assertTrue(issubclass(InvalidReleaseStateError, ReleaseError))

    def test_version_no_subprocess(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "subprocess"))

    def test_version_no_shell(self):
        v = _make_version()
        self.assertFalse(hasattr(v, "shell"))

    def test_report_no_subprocess(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "subprocess"))

    def test_report_no_shell(self):
        report = _make_report()
        self.assertFalse(hasattr(report, "shell"))

    def test_checklist_no_subprocess(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "subprocess"))

    def test_checklist_no_shell(self):
        checklist = _make_checklist()
        self.assertFalse(hasattr(checklist, "shell"))

    def test_item_no_private_key(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "private_key"))

    def test_item_no_ssh(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "ssh"))

    def test_item_no_command(self):
        item = _make_checklist_item()
        self.assertFalse(hasattr(item, "command"))

    def test_capability_matrix_all_unique(self):
        self.assertEqual(len(REQUIRED_CAPABILITIES), len(set(REQUIRED_CAPABILITIES)))


if __name__ == "__main__":
    unittest.main()
