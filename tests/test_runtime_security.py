"""
WorkOps Runtime Security Tests
Sprint057: Runtime Security Hardening Foundation

覆盖：
- SecurityLevel enum
- SecurityContext validation
- RuntimePermission enum
- CredentialAccessPolicy validation
- SecurityValidator contract
- RuntimeSecurityBoundary contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.security.model import SecurityLevel, SecurityContext
from backup_manager.security.policy import RuntimePermission, CredentialAccessPolicy
from backup_manager.security.validator import SecurityValidator, RuntimeSecurityBoundary
from backup_manager.security.errors import (
    SecurityError,
    InvalidSecurityContextError,
    SecurityViolationError,
    SecurityPolicyError,
)


# ============================================================================
# SecurityLevel
# ============================================================================

class TestSecurityLevel(unittest.TestCase):
    """安全级别测试"""

    def test_standard(self):
        self.assertEqual(SecurityLevel.STANDARD.value, "standard")

    def test_restricted(self):
        self.assertEqual(SecurityLevel.RESTRICTED.value, "restricted")

    def test_privileged(self):
        self.assertEqual(SecurityLevel.PRIVILEGED.value, "privileged")

    def test_three_levels(self):
        self.assertEqual(len(SecurityLevel), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            SecurityLevel("nonexistent")


# ============================================================================
# SecurityContext
# ============================================================================

class TestSecurityContext(unittest.TestCase):
    """安全上下文测试"""

    def _make_context(self, **kwargs):
        defaults = {
            "execution_id": "exec-001",
            "level": SecurityLevel.STANDARD,
        }
        defaults.update(kwargs)
        return SecurityContext(**defaults)

    def test_valid_context(self):
        ctx = self._make_context()
        self.assertEqual(ctx.execution_id, "exec-001")
        self.assertEqual(ctx.level, SecurityLevel.STANDARD)

    def test_frozen(self):
        ctx = self._make_context()
        with self.assertRaises(AttributeError):
            ctx.execution_id = "other"

    def test_slots(self):
        ctx = self._make_context()
        with self.assertRaises(AttributeError):
            ctx.__dict__

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidSecurityContextError):
            self._make_context(execution_id="")

    def test_invalid_level_rejected(self):
        with self.assertRaises(InvalidSecurityContextError):
            self._make_context(level="standard")

    def test_timezone_aware(self):
        ctx = self._make_context()
        self.assertIsNotNone(ctx.created_at.tzinfo)

    def test_all_levels(self):
        for level in SecurityLevel:
            ctx = self._make_context(level=level)
            self.assertEqual(ctx.level, level)

    def test_no_forbidden_fields(self):
        ctx = self._make_context()
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "private_key"]:
            self.assertFalse(hasattr(ctx, attr))

    def test_repr_no_secrets(self):
        ctx = self._make_context()
        r = repr(ctx)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RuntimePermission
# ============================================================================

class TestRuntimePermission(unittest.TestCase):
    """运行时权限测试"""

    def test_read(self):
        self.assertEqual(RuntimePermission.READ.value, "read")

    def test_execute(self):
        self.assertEqual(RuntimePermission.EXECUTE.value, "execute")

    def test_modify(self):
        self.assertEqual(RuntimePermission.MODIFY.value, "modify")

    def test_three_permissions(self):
        self.assertEqual(len(RuntimePermission), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RuntimePermission("nonexistent")


# ============================================================================
# CredentialAccessPolicy
# ============================================================================

class TestCredentialAccessPolicy(unittest.TestCase):
    """凭证访问策略测试"""

    def _make_policy(self, **kwargs):
        defaults = {
            "adapter_id": "linux-001",
            "allowed": True,
        }
        defaults.update(kwargs)
        return CredentialAccessPolicy(**defaults)

    def test_valid_policy(self):
        policy = self._make_policy()
        self.assertEqual(policy.adapter_id, "linux-001")
        self.assertTrue(policy.allowed)

    def test_frozen(self):
        policy = self._make_policy()
        with self.assertRaises(AttributeError):
            policy.adapter_id = "other"

    def test_slots(self):
        policy = self._make_policy()
        with self.assertRaises(AttributeError):
            policy.__dict__

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidSecurityContextError):
            self._make_policy(adapter_id="")

    def test_allowed_must_be_bool(self):
        with self.assertRaises(InvalidSecurityContextError):
            self._make_policy(allowed=1)

    def test_timezone_aware(self):
        policy = self._make_policy()
        self.assertIsNotNone(policy.created_at.tzinfo)

    def test_denied_policy(self):
        policy = self._make_policy(allowed=False)
        self.assertFalse(policy.allowed)

    def test_no_forbidden_fields(self):
        policy = self._make_policy()
        for attr in ["credential_value", "secret", "password", "token"]:
            self.assertFalse(hasattr(policy, attr))

    def test_repr_no_secrets(self):
        policy = self._make_policy()
        r = repr(policy)
        for term in ["password", "secret", "token", "credential_value"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# SecurityValidator Contract
# ============================================================================

class TestSecurityValidatorContract(unittest.TestCase):
    """安全验证器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(SecurityValidator, ABC))

    def test_has_validate(self):
        self.assertTrue(hasattr(SecurityValidator, "validate"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            SecurityValidator()

    def test_concrete_subclass(self):
        class MockValidator(SecurityValidator):
            def validate(self, context):
                return context.level == SecurityLevel.STANDARD
        validator = MockValidator()
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        self.assertTrue(validator.validate(ctx))

    def test_missing_validate(self):
        class BadValidator(SecurityValidator):
            pass
        with self.assertRaises(TypeError):
            BadValidator()


# ============================================================================
# RuntimeSecurityBoundary Contract
# ============================================================================

class TestRuntimeSecurityBoundaryContract(unittest.TestCase):
    """运行时安全边界契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RuntimeSecurityBoundary, ABC))

    def test_has_check(self):
        self.assertTrue(hasattr(RuntimeSecurityBoundary, "check"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RuntimeSecurityBoundary()

    def test_concrete_subclass(self):
        class MockBoundary(RuntimeSecurityBoundary):
            def check(self, permission):
                return permission == RuntimePermission.READ
        boundary = MockBoundary()
        self.assertTrue(boundary.check(RuntimePermission.READ))
        self.assertFalse(boundary.check(RuntimePermission.EXECUTE))

    def test_missing_check(self):
        class BadBoundary(RuntimeSecurityBoundary):
            pass
        with self.assertRaises(TypeError):
            BadBoundary()


# ============================================================================
# Error Model
# ============================================================================

class TestSecurityErrors(unittest.TestCase):
    """错误模型测试"""

    def test_security_error(self):
        with self.assertRaises(SecurityError):
            raise SecurityError("test")

    def test_invalid_context_error(self):
        with self.assertRaises(SecurityError):
            raise InvalidSecurityContextError("test")

    def test_violation_error(self):
        with self.assertRaises(SecurityError):
            raise SecurityViolationError("test")

    def test_policy_error(self):
        with self.assertRaises(SecurityError):
            raise SecurityPolicyError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (SecurityError, ("test",)),
            (InvalidSecurityContextError, ("test",)),
            (SecurityViolationError, ("test",)),
            (SecurityPolicyError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_context_no_credentials(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "private_key"]:
            self.assertFalse(hasattr(ctx, attr))

    def test_policy_no_credentials(self):
        policy = CredentialAccessPolicy(adapter_id="linux-001", allowed=True)
        for attr in ["credential_value", "secret", "password", "token"]:
            self.assertFalse(hasattr(policy, attr))

    def test_no_subprocess(self):
        import ast
        import os
        sec_dir = os.path.join("backup_manager", "security")
        for filename in os.listdir(sec_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(sec_dir, filename)
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
        sec_dir = os.path.join("backup_manager", "security")
        for filename in os.listdir(sec_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(sec_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_validator_lifecycle(self):
        """完整验证器生命周期"""
        class MockValidator(SecurityValidator):
            def validate(self, context):
                return context.level == SecurityLevel.STANDARD
        validator = MockValidator()
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        self.assertTrue(validator.validate(ctx))

    def test_boundary_lifecycle(self):
        """完整边界生命周期"""
        class MockBoundary(RuntimeSecurityBoundary):
            def check(self, permission):
                return permission == RuntimePermission.READ
        boundary = MockBoundary()
        self.assertTrue(boundary.check(RuntimePermission.READ))
        self.assertFalse(boundary.check(RuntimePermission.MODIFY))


# ============================================================================
# Extended Tests
# ============================================================================

class TestRuntimeSecurityExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidSecurityContextError, SecurityError))
        self.assertTrue(issubclass(SecurityViolationError, SecurityError))
        self.assertTrue(issubclass(SecurityPolicyError, SecurityError))

    def test_context_repr_no_secrets(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        r = repr(ctx)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_policy_repr_no_secrets(self):
        policy = CredentialAccessPolicy(adapter_id="linux-001", allowed=True)
        r = repr(policy)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_context_preserves_all_fields(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.RESTRICTED)
        self.assertEqual(ctx.execution_id, "exec-001")
        self.assertEqual(ctx.level, SecurityLevel.RESTRICTED)

    def test_policy_preserves_all_fields(self):
        policy = CredentialAccessPolicy(adapter_id="linux-001", allowed=False)
        self.assertEqual(policy.adapter_id, "linux-001")
        self.assertFalse(policy.allowed)

    def test_validator_returns_bool(self):
        class MockValidator(SecurityValidator):
            def validate(self, context):
                return True
        validator = MockValidator()
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        result = validator.validate(ctx)
        self.assertIsInstance(result, bool)

    def test_boundary_returns_bool(self):
        class MockBoundary(RuntimeSecurityBoundary):
            def check(self, permission):
                return True
        boundary = MockBoundary()
        result = boundary.check(RuntimePermission.READ)
        self.assertIsInstance(result, bool)

    def test_context_whitespace_id_rejected(self):
        with self.assertRaises(InvalidSecurityContextError):
            SecurityContext(execution_id="   ", level=SecurityLevel.STANDARD)

    def test_policy_whitespace_adapter_id_rejected(self):
        with self.assertRaises(InvalidSecurityContextError):
            CredentialAccessPolicy(adapter_id="   ", allowed=True)

    def test_context_no_command(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        self.assertFalse(hasattr(ctx, "command"))

    def test_context_no_ssh(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        self.assertFalse(hasattr(ctx, "ssh"))

    def test_context_no_private_key(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        self.assertFalse(hasattr(ctx, "private_key"))

    def test_error_messages_safe(self):
        try:
            raise SecurityError("test")
        except SecurityError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_violation_error_message(self):
        exc = SecurityViolationError("violation")
        self.assertIn("violation", str(exc))

    def test_policy_error_message(self):
        exc = SecurityPolicyError("policy error")
        self.assertIn("policy error", str(exc))

    def test_context_all_levels(self):
        for level in SecurityLevel:
            ctx = SecurityContext(execution_id="exec-001", level=level)
            self.assertEqual(ctx.level, level)

    def test_policy_all_permissions(self):
        for perm in RuntimePermission:
            self.assertIsInstance(perm.value, str)

    def test_validator_restricted_rejected(self):
        class MockValidator(SecurityValidator):
            def validate(self, context):
                return context.level != SecurityLevel.PRIVILEGED
        validator = MockValidator()
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.PRIVILEGED)
        self.assertFalse(validator.validate(ctx))

    def test_boundary_all_permissions(self):
        class MockBoundary(RuntimeSecurityBoundary):
            def check(self, permission):
                return permission in (RuntimePermission.READ, RuntimePermission.EXECUTE)
        boundary = MockBoundary()
        self.assertTrue(boundary.check(RuntimePermission.READ))
        self.assertTrue(boundary.check(RuntimePermission.EXECUTE))
        self.assertFalse(boundary.check(RuntimePermission.MODIFY))

    def test_context_no_token(self):
        ctx = SecurityContext(execution_id="exec-001", level=SecurityLevel.STANDARD)
        self.assertFalse(hasattr(ctx, "token"))

    def test_policy_no_password(self):
        policy = CredentialAccessPolicy(adapter_id="linux-001", allowed=True)
        self.assertFalse(hasattr(policy, "password"))


if __name__ == "__main__":
    unittest.main()
