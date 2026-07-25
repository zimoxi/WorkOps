"""
WorkOps Release Candidate Tests
Sprint065: Release Candidate Foundation

覆盖：
- ReleaseVersion validation
- BuildMetadata validation
- CapabilityReport validation
- ReleaseCheckResult validation
- ReleaseValidator contract
- Error model
- Security boundary
- Full integration validation
"""

import unittest
from datetime import datetime, timezone

from backup_manager.release.version import ReleaseVersion
from backup_manager.release.metadata import BuildMetadata
from backup_manager.release.capability import CapabilityReport
from backup_manager.release.validator import ReleaseCheckResult, ReleaseValidator
from backup_manager.release.errors import (
    ReleaseError,
    InvalidReleaseMetadataError,
    ReleaseValidationError,
    ReleaseUnavailableError,
)


# ============================================================================
# ReleaseVersion
# ============================================================================

class TestReleaseVersion(unittest.TestCase):
    """发布版本测试"""

    def test_valid_version(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 0)
        self.assertEqual(v.patch, 0)
        self.assertEqual(v.stage, "rc1")

    def test_str(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        self.assertEqual(str(v), "1.0.0-rc1")

    def test_frozen(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        with self.assertRaises(AttributeError):
            v.major = 2

    def test_slots(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        with self.assertRaises(AttributeError):
            v.__dict__

    def test_negative_major_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseVersion(major=-1, minor=0, patch=0, stage="rc1")

    def test_negative_minor_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseVersion(major=1, minor=-1, patch=0, stage="rc1")

    def test_negative_patch_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseVersion(major=1, minor=0, patch=-1, stage="rc1")

    def test_empty_stage_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseVersion(major=1, minor=0, patch=0, stage="")

    def test_zero_version_allowed(self):
        v = ReleaseVersion(major=0, minor=0, patch=0, stage="alpha")
        self.assertEqual(v.major, 0)

    def test_large_version_allowed(self):
        v = ReleaseVersion(major=99, minor=99, patch=99, stage="release")
        self.assertEqual(v.major, 99)

    def test_no_forbidden_fields(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(v, attr))

    def test_repr_no_secrets(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        r = repr(v)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# BuildMetadata
# ============================================================================

class TestBuildMetadata(unittest.TestCase):
    """构建元数据测试"""

    def _make_metadata(self, **kwargs):
        version = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        defaults = {"version": version, "build_id": "build-001"}
        defaults.update(kwargs)
        return BuildMetadata(**defaults)

    def test_valid_metadata(self):
        meta = self._make_metadata()
        self.assertEqual(meta.version.major, 1)
        self.assertEqual(meta.build_id, "build-001")

    def test_frozen(self):
        meta = self._make_metadata()
        with self.assertRaises(AttributeError):
            meta.build_id = "other"

    def test_slots(self):
        meta = self._make_metadata()
        with self.assertRaises(AttributeError):
            meta.__dict__

    def test_invalid_version_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            BuildMetadata(version="1.0.0", build_id="build-001")

    def test_empty_build_id_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            self._make_metadata(build_id="")

    def test_timezone_aware(self):
        meta = self._make_metadata()
        self.assertIsNotNone(meta.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        meta = self._make_metadata()
        for attr in ["password", "secret", "token", "command"]:
            self.assertFalse(hasattr(meta, attr))

    def test_repr_no_secrets(self):
        meta = self._make_metadata()
        r = repr(meta)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# CapabilityReport
# ============================================================================

class TestCapabilityReport(unittest.TestCase):
    """能力报告测试"""

    def _make_report(self, **kwargs):
        defaults = {
            "platform_name": "WorkOps",
            "capabilities": ("backup", "restore", "health", "metrics"),
        }
        defaults.update(kwargs)
        return CapabilityReport(**defaults)

    def test_valid_report(self):
        report = self._make_report()
        self.assertEqual(report.platform_name, "WorkOps")
        self.assertEqual(len(report.capabilities), 4)

    def test_frozen(self):
        report = self._make_report()
        with self.assertRaises(AttributeError):
            report.platform_name = "other"

    def test_slots(self):
        report = self._make_report()
        with self.assertRaises(AttributeError):
            report.__dict__

    def test_empty_platform_name_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            self._make_report(platform_name="")

    def test_empty_capabilities_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            self._make_report(capabilities=())

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            self._make_report(capabilities=["backup", "restore"])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            self._make_report(capabilities=("",))

    def test_timezone_aware(self):
        report = self._make_report()
        self.assertIsNotNone(report.generated_at.tzinfo)

    def test_single_capability(self):
        report = self._make_report(capabilities=("backup",))
        self.assertEqual(len(report.capabilities), 1)

    def test_no_forbidden_fields(self):
        report = self._make_report()
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(report, attr))

    def test_repr_no_secrets(self):
        report = self._make_report()
        r = repr(report)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# ReleaseCheckResult
# ============================================================================

class TestReleaseCheckResult(unittest.TestCase):
    """发布检查结果测试"""

    def test_valid_result(self):
        result = ReleaseCheckResult(success=True, message="ok")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    def test_frozen(self):
        result = ReleaseCheckResult(success=True, message="ok")
        with self.assertRaises(AttributeError):
            result.success = False

    def test_slots(self):
        result = ReleaseCheckResult(success=True, message="ok")
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseCheckResult(success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            ReleaseCheckResult(success=True, message=123)

    def test_timezone_aware(self):
        result = ReleaseCheckResult(success=True, message="ok")
        self.assertIsNotNone(result.checked_at.tzinfo)

    def test_failed_result(self):
        result = ReleaseCheckResult(success=False, message="failed")
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = ReleaseCheckResult(success=True, message="ok")
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# ReleaseValidator Contract
# ============================================================================

class TestReleaseValidatorContract(unittest.TestCase):
    """发布验证器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(ReleaseValidator, ABC))

    def test_has_validate(self):
        self.assertTrue(hasattr(ReleaseValidator, "validate"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ReleaseValidator()

    def test_concrete_subclass(self):
        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return len(report.capabilities) >= 3
        validator = MockValidator()
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore", "health"),
        )
        self.assertTrue(validator.validate(report))

    def test_missing_validate(self):
        class BadValidator(ReleaseValidator):
            pass
        with self.assertRaises(TypeError):
            BadValidator()


# ============================================================================
# Error Model
# ============================================================================

class TestReleaseErrors(unittest.TestCase):
    """错误模型测试"""

    def test_release_error(self):
        with self.assertRaises(ReleaseError):
            raise ReleaseError("test")

    def test_invalid_metadata_error(self):
        with self.assertRaises(ReleaseError):
            raise InvalidReleaseMetadataError("test")

    def test_validation_error(self):
        with self.assertRaises(ReleaseError):
            raise ReleaseValidationError("test")

    def test_unavailable_error(self):
        with self.assertRaises(ReleaseError):
            raise ReleaseUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (ReleaseError, ("test",)),
            (InvalidReleaseMetadataError, ("test",)),
            (ReleaseValidationError, ("test",)),
            (ReleaseUnavailableError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_version_no_credentials(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(v, attr))

    def test_metadata_no_credentials(self):
        meta = BuildMetadata(
            version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
            build_id="build-001",
        )
        for attr in ["password", "secret", "token", "command"]:
            self.assertFalse(hasattr(meta, attr))

    def test_report_no_credentials(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore"),
        )
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(report, attr))

    def test_result_no_credentials(self):
        result = ReleaseCheckResult(success=True, message="ok")
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        release_dir = os.path.join("backup_manager", "release")
        for filename in os.listdir(release_dir):
            if not filename.endswith(".py"):
                continue
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
        for filename in os.listdir(release_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(release_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_validator_lifecycle(self):
        """完整验证器生命周期"""
        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return len(report.capabilities) >= 3
        validator = MockValidator()
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore", "health", "metrics", "api"),
        )
        self.assertTrue(validator.validate(report))


# ============================================================================
# Extended Tests
# ============================================================================

class TestReleaseCandidateExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidReleaseMetadataError, ReleaseError))
        self.assertTrue(issubclass(ReleaseValidationError, ReleaseError))
        self.assertTrue(issubclass(ReleaseUnavailableError, ReleaseError))

    def test_version_str_format(self):
        v = ReleaseVersion(major=2, minor=1, patch=3, stage="beta")
        self.assertEqual(str(v), "2.1.3-beta")

    def test_version_repr_no_secrets(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        r = repr(v)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_metadata_repr_no_secrets(self):
        meta = BuildMetadata(
            version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
            build_id="build-001",
        )
        r = repr(meta)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_report_repr_no_secrets(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore"),
        )
        r = repr(report)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = ReleaseCheckResult(success=True, message="ok")
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_version_preserves_all_fields(self):
        v = ReleaseVersion(major=1, minor=2, patch=3, stage="rc1")
        self.assertEqual(v.major, 1)
        self.assertEqual(v.minor, 2)
        self.assertEqual(v.patch, 3)
        self.assertEqual(v.stage, "rc1")

    def test_metadata_preserves_all_fields(self):
        version = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        meta = BuildMetadata(version=version, build_id="build-001")
        self.assertIs(meta.version, version)
        self.assertEqual(meta.build_id, "build-001")

    def test_report_preserves_all_fields(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore"),
        )
        self.assertEqual(report.platform_name, "WorkOps")
        self.assertEqual(report.capabilities, ("backup", "restore"))

    def test_validator_returns_bool(self):
        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return True
        validator = MockValidator()
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup",),
        )
        result = validator.validate(report)
        self.assertIsInstance(result, bool)

    def test_validator_rejects_insufficient(self):
        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return len(report.capabilities) >= 5
        validator = MockValidator()
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore"),
        )
        self.assertFalse(validator.validate(report))

    def test_version_no_password(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        self.assertFalse(hasattr(v, "password"))

    def test_version_no_secret(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        self.assertFalse(hasattr(v, "secret"))

    def test_version_no_token(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        self.assertFalse(hasattr(v, "token"))

    def test_metadata_no_password(self):
        meta = BuildMetadata(
            version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
            build_id="build-001",
        )
        self.assertFalse(hasattr(meta, "password"))

    def test_metadata_no_secret(self):
        meta = BuildMetadata(
            version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
            build_id="build-001",
        )
        self.assertFalse(hasattr(meta, "secret"))

    def test_metadata_no_command(self):
        meta = BuildMetadata(
            version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
            build_id="build-001",
        )
        self.assertFalse(hasattr(meta, "command"))

    def test_report_no_password(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup",),
        )
        self.assertFalse(hasattr(report, "password"))

    def test_report_no_secret(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup",),
        )
        self.assertFalse(hasattr(report, "secret"))

    def test_result_no_password(self):
        result = ReleaseCheckResult(success=True, message="ok")
        self.assertFalse(hasattr(result, "password"))

    def test_result_no_secret(self):
        result = ReleaseCheckResult(success=True, message="ok")
        self.assertFalse(hasattr(result, "secret"))

    def test_error_messages_safe(self):
        try:
            raise ReleaseError("test")
        except ReleaseError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_validation_error_message(self):
        exc = ReleaseValidationError("validation failed")
        self.assertIn("validation failed", str(exc))

    def test_unavailable_error_message(self):
        exc = ReleaseUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_metadata_whitespace_build_id_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            BuildMetadata(
                version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
                build_id="   ",
            )

    def test_report_whitespace_platform_name_rejected(self):
        with self.assertRaises(InvalidReleaseMetadataError):
            CapabilityReport(
                platform_name="   ",
                capabilities=("backup",),
            )

    def test_report_multiple_capabilities(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=(
                "linux_runtime", "pve_runtime", "omv_runtime",
                "backup", "restore", "health", "metrics", "api",
            ),
        )
        self.assertEqual(len(report.capabilities), 8)

    def test_result_empty_message_accepted(self):
        result = ReleaseCheckResult(success=True, message="")
        self.assertEqual(result.message, "")

    def test_version_stage_types(self):
        for stage in ["alpha", "beta", "rc1", "rc2", "release", "stable"]:
            v = ReleaseVersion(major=1, minor=0, patch=0, stage=stage)
            self.assertEqual(v.stage, stage)

    def test_version_all_zero(self):
        v = ReleaseVersion(major=0, minor=0, patch=0, stage="dev")
        self.assertEqual(str(v), "0.0.0-dev")

    def test_version_large_numbers(self):
        v = ReleaseVersion(major=999, minor=999, patch=999, stage="rc")
        self.assertEqual(str(v), "999.999.999-rc")

    def test_metadata_with_different_versions(self):
        for major in [0, 1, 2]:
            v = ReleaseVersion(major=major, minor=0, patch=0, stage="rc1")
            meta = BuildMetadata(version=v, build_id=f"build-{major}")
            self.assertEqual(meta.version.major, major)

    def test_report_single_capability(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup",),
        )
        self.assertEqual(len(report.capabilities), 1)

    def test_report_many_capabilities(self):
        caps = tuple(f"cap_{i}" for i in range(20))
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=caps,
        )
        self.assertEqual(len(report.capabilities), 20)

    def test_validator_accept(self):
        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return "backup" in report.capabilities
        validator = MockValidator()
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore"),
        )
        self.assertTrue(validator.validate(report))

    def test_validator_reject(self):
        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return "nonexistent" in report.capabilities
        validator = MockValidator()
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup", "restore"),
        )
        self.assertFalse(validator.validate(report))

    def test_result_success_true(self):
        result = ReleaseCheckResult(success=True, message="ok")
        self.assertTrue(result.success)

    def test_result_success_false(self):
        result = ReleaseCheckResult(success=False, message="failed")
        self.assertFalse(result.success)

    def test_version_no_credential(self):
        v = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        self.assertFalse(hasattr(v, "credential"))

    def test_metadata_no_credential(self):
        meta = BuildMetadata(
            version=ReleaseVersion(major=1, minor=0, patch=0, stage="rc1"),
            build_id="build-001",
        )
        self.assertFalse(hasattr(meta, "credential"))

    def test_report_no_credential(self):
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=("backup",),
        )
        self.assertFalse(hasattr(report, "credential"))


# ============================================================================
# Full Integration Validation
# ============================================================================

class TestFullIntegrationValidation(unittest.TestCase):
    """全量集成验证"""

    def test_version_model_chain(self):
        """版本→构建元数据→能力报告→验证"""
        version = ReleaseVersion(major=1, minor=0, patch=0, stage="rc1")
        meta = BuildMetadata(version=version, build_id="build-001")
        report = CapabilityReport(
            platform_name="WorkOps",
            capabilities=(
                "linux_runtime", "pve_runtime", "omv_runtime",
                "backup", "restore", "health", "metrics", "api",
            ),
        )

        class MockValidator(ReleaseValidator):
            def validate(self, report):
                return len(report.capabilities) >= 5

        validator = MockValidator()
        self.assertTrue(validator.validate(report))
        self.assertEqual(meta.version.stage, "rc1")

    def test_release_check_result_chain(self):
        """验证结果链"""
        result = ReleaseCheckResult(success=True, message="all checks passed")
        self.assertTrue(result.success)
        self.assertIn("passed", result.message)

    def test_architecture_layers_present(self):
        """确认架构层存在"""
        import importlib
        layers = [
            "backup_manager.api",
            "backup_manager.operations",
            "backup_manager.jobs",
            "backup_manager.transaction",
            "backup_manager.security",
            "backup_manager.runtime",
            "backup_manager.runtime_context",
            "backup_manager.adapters",
            "backup_manager.backup",
            "backup_manager.restore_workflow",
            "backup_manager.health",
            "backup_manager.metrics",
            "backup_manager.audit",
            "backup_manager.release",
        ]
        for layer in layers:
            try:
                importlib.import_module(layer)
            except ImportError:
                self.fail(f"Architecture layer missing: {layer}")


if __name__ == "__main__":
    unittest.main()
