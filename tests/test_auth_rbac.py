"""
WorkOps Authentication RBAC Tests
Sprint072: Authentication RBAC Foundation

覆盖：
- Identity validation
- RoleType enum, Role validation
- PermissionType enum, Permission validation
- AuthenticationProvider contract
- AuthorizationGuard contract
- AuthorizationResult validation
- Error model
- Security boundary
"""

import unittest

from backup_manager.auth.identity import Identity
from backup_manager.auth.role import RoleType, Role
from backup_manager.auth.permission import PermissionType, Permission
from backup_manager.auth.authentication import AuthenticationProvider
from backup_manager.auth.authorization import AuthorizationGuard, AuthorizationResult
from backup_manager.auth.errors import (
    AuthError,
    AuthenticationFailedError,
    AuthorizationDeniedError,
    InvalidIdentityError,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_identity(**kwargs):
    defaults = {"identity_id": "id-001", "username": "admin"}
    defaults.update(kwargs)
    return Identity(**defaults)


def _make_role(**kwargs):
    defaults = {"role_id": "role-001", "role_type": RoleType.ADMIN}
    defaults.update(kwargs)
    return Role(**defaults)


def _make_permission(**kwargs):
    defaults = {"permission_id": "perm-001", "permission_type": PermissionType.READ}
    defaults.update(kwargs)
    return Permission(**defaults)


def _make_auth_result(**kwargs):
    defaults = {"allowed": True, "reason": "granted"}
    defaults.update(kwargs)
    return AuthorizationResult(**defaults)


# ============================================================================
# Identity
# ============================================================================

class TestIdentity(unittest.TestCase):
    """身份模型测试"""

    def test_valid_identity(self):
        identity = _make_identity()
        self.assertEqual(identity.identity_id, "id-001")
        self.assertEqual(identity.username, "admin")

    def test_frozen(self):
        identity = _make_identity()
        with self.assertRaises(AttributeError):
            identity.identity_id = "other"

    def test_slots(self):
        identity = _make_identity()
        with self.assertRaises(AttributeError):
            identity.__dict__

    def test_empty_identity_id_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_identity(identity_id="")

    def test_empty_username_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_identity(username="")

    def test_timezone_aware(self):
        identity = _make_identity()
        self.assertIsNotNone(identity.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        identity = _make_identity()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(identity, attr))

    def test_repr_no_secrets(self):
        identity = _make_identity()
        r = repr(identity)
        for term in ["password", "secret", "token", "credential", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RoleType & Role
# ============================================================================

class TestRoleType(unittest.TestCase):
    """角色类型测试"""

    def test_admin(self):
        self.assertEqual(RoleType.ADMIN.value, "admin")

    def test_operator(self):
        self.assertEqual(RoleType.OPERATOR.value, "operator")

    def test_viewer(self):
        self.assertEqual(RoleType.VIEWER.value, "viewer")

    def test_three_types(self):
        self.assertEqual(len(RoleType), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RoleType("nonexistent")


class TestRole(unittest.TestCase):
    """角色模型测试"""

    def test_valid_role(self):
        role = _make_role()
        self.assertEqual(role.role_id, "role-001")
        self.assertEqual(role.role_type, RoleType.ADMIN)

    def test_frozen(self):
        role = _make_role()
        with self.assertRaises(AttributeError):
            role.role_id = "other"

    def test_slots(self):
        role = _make_role()
        with self.assertRaises(AttributeError):
            role.__dict__

    def test_empty_role_id_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_role(role_id="")

    def test_invalid_role_type_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_role(role_type="admin")

    def test_all_role_types(self):
        for rt in RoleType:
            role = _make_role(role_type=rt)
            self.assertEqual(role.role_type, rt)


# ============================================================================
# PermissionType & Permission
# ============================================================================

class TestPermissionType(unittest.TestCase):
    """权限类型测试"""

    def test_read(self):
        self.assertEqual(PermissionType.READ.value, "read")

    def test_execute(self):
        self.assertEqual(PermissionType.EXECUTE.value, "execute")

    def test_backup(self):
        self.assertEqual(PermissionType.BACKUP.value, "backup")

    def test_restore(self):
        self.assertEqual(PermissionType.RESTORE.value, "restore")

    def test_admin(self):
        self.assertEqual(PermissionType.ADMIN.value, "admin")

    def test_five_types(self):
        self.assertEqual(len(PermissionType), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PermissionType("nonexistent")


class TestPermission(unittest.TestCase):
    """权限模型测试"""

    def test_valid_permission(self):
        perm = _make_permission()
        self.assertEqual(perm.permission_id, "perm-001")
        self.assertEqual(perm.permission_type, PermissionType.READ)

    def test_frozen(self):
        perm = _make_permission()
        with self.assertRaises(AttributeError):
            perm.permission_id = "other"

    def test_slots(self):
        perm = _make_permission()
        with self.assertRaises(AttributeError):
            perm.__dict__

    def test_empty_permission_id_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_permission(permission_id="")

    def test_invalid_permission_type_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_permission(permission_type="read")

    def test_all_permission_types(self):
        for pt in PermissionType:
            perm = _make_permission(permission_type=pt)
            self.assertEqual(perm.permission_type, pt)


# ============================================================================
# AuthenticationProvider Contract
# ============================================================================

class TestAuthenticationProviderContract(unittest.TestCase):
    """认证提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AuthenticationProvider, ABC))

    def test_has_authenticate(self):
        self.assertTrue(hasattr(AuthenticationProvider, "authenticate"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AuthenticationProvider()

    def test_concrete_subclass(self):
        class MockProvider(AuthenticationProvider):
            def authenticate(self, identity_data):
                return Identity(
                    identity_id="id-001",
                    username=identity_data.get("username", "unknown"),
                )
        provider = MockProvider()
        identity = provider.authenticate({"username": "admin"})
        self.assertEqual(identity.username, "admin")

    def test_missing_authenticate(self):
        class BadProvider(AuthenticationProvider):
            pass
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# AuthorizationGuard Contract
# ============================================================================

class TestAuthorizationGuardContract(unittest.TestCase):
    """授权守卫契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AuthorizationGuard, ABC))

    def test_has_authorize(self):
        self.assertTrue(hasattr(AuthorizationGuard, "authorize"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AuthorizationGuard()

    def test_concrete_subclass(self):
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=True, reason="granted",
                )
        guard = MockGuard()
        identity = _make_identity()
        perm = _make_permission()
        result = guard.authorize(identity, perm)
        self.assertTrue(result.allowed)

    def test_missing_authorize(self):
        class BadGuard(AuthorizationGuard):
            pass
        with self.assertRaises(TypeError):
            BadGuard()


# ============================================================================
# AuthorizationResult
# ============================================================================

class TestAuthorizationResult(unittest.TestCase):
    """授权结果测试"""

    def test_valid_result(self):
        result = _make_auth_result()
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "granted")

    def test_frozen(self):
        result = _make_auth_result()
        with self.assertRaises(AttributeError):
            result.allowed = False

    def test_slots(self):
        result = _make_auth_result()
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_allowed_must_be_bool(self):
        with self.assertRaises(InvalidIdentityError):
            AuthorizationResult(allowed=1, reason="ok")

    def test_reason_must_be_str(self):
        with self.assertRaises(InvalidIdentityError):
            AuthorizationResult(allowed=True, reason=123)

    def test_timezone_aware(self):
        result = _make_auth_result()
        self.assertIsNotNone(result.checked_at.tzinfo)

    def test_denied_result(self):
        result = _make_auth_result(allowed=False, reason="denied")
        self.assertFalse(result.allowed)

    def test_no_forbidden_fields(self):
        result = _make_auth_result()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestAuthErrors(unittest.TestCase):
    """错误模型测试"""

    def test_auth_error(self):
        with self.assertRaises(AuthError):
            raise AuthError("test")

    def test_authentication_failed_error(self):
        with self.assertRaises(AuthError):
            raise AuthenticationFailedError("test")

    def test_authorization_denied_error(self):
        with self.assertRaises(AuthError):
            raise AuthorizationDeniedError("test")

    def test_invalid_identity_error(self):
        with self.assertRaises(AuthError):
            raise InvalidIdentityError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (AuthError, ("test",)),
            (AuthenticationFailedError, ("test",)),
            (AuthorizationDeniedError, ("test",)),
            (InvalidIdentityError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_identity_no_credentials(self):
        identity = _make_identity()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(identity, attr))

    def test_role_no_credentials(self):
        role = _make_role()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(role, attr))

    def test_permission_no_credentials(self):
        perm = _make_permission()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(perm, attr))

    def test_result_no_credentials(self):
        result = _make_auth_result()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        auth_dir = os.path.join("backup_manager", "auth")
        for filename in os.listdir(auth_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(auth_dir, filename)
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
        auth_dir = os.path.join("backup_manager", "auth")
        for filename in os.listdir(auth_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(auth_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_full_lifecycle(self):
        """完整认证授权生命周期"""
        class MockProvider(AuthenticationProvider):
            def authenticate(self, identity_data):
                return Identity(
                    identity_id="id-001",
                    username=identity_data.get("username", "unknown"),
                )
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=True, reason="granted",
                )
        provider = MockProvider()
        guard = MockGuard()
        identity = provider.authenticate({"username": "admin"})
        perm = _make_permission()
        result = guard.authorize(identity, perm)
        self.assertTrue(result.allowed)


# ============================================================================
# Extended Tests
# ============================================================================

class TestAuthRBACExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(AuthenticationFailedError, AuthError))
        self.assertTrue(issubclass(AuthorizationDeniedError, AuthError))
        self.assertTrue(issubclass(InvalidIdentityError, AuthError))

    def test_identity_preserves_all_fields(self):
        identity = _make_identity()
        self.assertEqual(identity.identity_id, "id-001")
        self.assertEqual(identity.username, "admin")

    def test_role_preserves_all_fields(self):
        role = _make_role()
        self.assertEqual(role.role_id, "role-001")
        self.assertEqual(role.role_type, RoleType.ADMIN)

    def test_permission_preserves_all_fields(self):
        perm = _make_permission()
        self.assertEqual(perm.permission_id, "perm-001")
        self.assertEqual(perm.permission_type, PermissionType.READ)

    def test_result_preserves_all_fields(self):
        result = _make_auth_result()
        self.assertTrue(result.allowed)
        self.assertEqual(result.reason, "granted")

    def test_identity_repr_no_secrets(self):
        identity = _make_identity()
        r = repr(identity)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_role_repr_no_secrets(self):
        role = _make_role()
        r = repr(role)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_permission_repr_no_secrets(self):
        perm = _make_permission()
        r = repr(perm)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = _make_auth_result()
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_identity_no_password(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "password"))

    def test_identity_no_secret(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "secret"))

    def test_identity_no_token(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "token"))

    def test_identity_no_credential(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "credential"))

    def test_identity_no_private_key(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "private_key"))

    def test_identity_whitespace_id_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_identity(identity_id="   ")

    def test_identity_whitespace_username_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_identity(username="   ")

    def test_role_whitespace_id_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_role(role_id="   ")

    def test_permission_whitespace_id_rejected(self):
        with self.assertRaises(InvalidIdentityError):
            _make_permission(permission_id="   ")

    def test_result_empty_reason_accepted(self):
        result = AuthorizationResult(allowed=True, reason="")
        self.assertEqual(result.reason, "")

    def test_identity_different_usernames(self):
        for name in ["admin", "operator", "viewer", "user123"]:
            identity = _make_identity(username=name)
            self.assertEqual(identity.username, name)

    def test_role_all_types(self):
        for rt in RoleType:
            role = _make_role(role_type=rt)
            self.assertEqual(role.role_type, rt)

    def test_permission_all_types(self):
        for pt in PermissionType:
            perm = _make_permission(permission_type=pt)
            self.assertEqual(perm.permission_type, pt)

    def test_authenticate_returns_identity(self):
        class MockProvider(AuthenticationProvider):
            def authenticate(self, identity_data):
                return Identity(
                    identity_id="id-001",
                    username="admin",
                )
        provider = MockProvider()
        identity = provider.authenticate({})
        self.assertIsInstance(identity, Identity)

    def test_authorize_returns_result(self):
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=True, reason="granted",
                )
        guard = MockGuard()
        result = guard.authorize(_make_identity(), _make_permission())
        self.assertIsInstance(result, AuthorizationResult)

    def test_authorize_denied(self):
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=False, reason="insufficient permissions",
                )
        guard = MockGuard()
        result = guard.authorize(_make_identity(), _make_permission())
        self.assertFalse(result.allowed)

    def test_error_messages_safe(self):
        try:
            raise AuthError("test")
        except AuthError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_auth_failed_error_message(self):
        exc = AuthenticationFailedError("auth failed")
        self.assertIn("auth failed", str(exc))

    def test_auth_denied_error_message(self):
        exc = AuthorizationDeniedError("access denied")
        self.assertIn("access denied", str(exc))

    def test_invalid_identity_error_message(self):
        exc = InvalidIdentityError("invalid identity")
        self.assertIn("invalid identity", str(exc))

    def test_identity_created_at_type(self):
        from datetime import datetime
        identity = _make_identity()
        self.assertIsInstance(identity.created_at, datetime)

    def test_result_checked_at_type(self):
        from datetime import datetime
        result = _make_auth_result()
        self.assertIsInstance(result.checked_at, datetime)

    def test_role_type_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(RoleType, Enum))

    def test_permission_type_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(PermissionType, Enum))

    def test_error_hierarchy_deep(self):
        self.assertTrue(issubclass(AuthError, Exception))
        self.assertTrue(issubclass(AuthenticationFailedError, Exception))
        self.assertTrue(issubclass(AuthorizationDeniedError, Exception))
        self.assertTrue(issubclass(InvalidIdentityError, Exception))

    def test_identity_no_ssh(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "ssh"))

    def test_identity_no_command(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "command"))

    def test_result_no_password(self):
        result = _make_auth_result()
        self.assertFalse(hasattr(result, "password"))

    def test_result_no_secret(self):
        result = _make_auth_result()
        self.assertFalse(hasattr(result, "secret"))

    def test_result_no_token(self):
        result = _make_auth_result()
        self.assertFalse(hasattr(result, "token"))

    def test_result_no_credential(self):
        result = _make_auth_result()
        self.assertFalse(hasattr(result, "credential"))

    def test_identity_all_fields_present(self):
        identity = _make_identity()
        self.assertTrue(hasattr(identity, "identity_id"))
        self.assertTrue(hasattr(identity, "username"))
        self.assertTrue(hasattr(identity, "created_at"))

    def test_role_all_fields_present(self):
        role = _make_role()
        self.assertTrue(hasattr(role, "role_id"))
        self.assertTrue(hasattr(role, "role_type"))

    def test_permission_all_fields_present(self):
        perm = _make_permission()
        self.assertTrue(hasattr(perm, "permission_id"))
        self.assertTrue(hasattr(perm, "permission_type"))

    def test_result_all_fields_present(self):
        result = _make_auth_result()
        self.assertTrue(hasattr(result, "allowed"))
        self.assertTrue(hasattr(result, "reason"))
        self.assertTrue(hasattr(result, "checked_at"))

    def test_result_allowed_bool_check(self):
        result = _make_auth_result()
        self.assertIsInstance(result.allowed, bool)

    def test_auth_provider_returns_identity(self):
        class MockProvider(AuthenticationProvider):
            def authenticate(self, identity_data):
                return Identity(
                    identity_id="id-001",
                    username="admin",
                )
        provider = MockProvider()
        result = provider.authenticate({})
        self.assertIsInstance(result, Identity)

    def test_guard_returns_result(self):
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=True, reason="granted",
                )
        guard = MockGuard()
        result = guard.authorize(_make_identity(), _make_permission())
        self.assertIsInstance(result, AuthorizationResult)

    def test_guard_denied_returns_result(self):
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=False, reason="denied",
                )
        guard = MockGuard()
        result = guard.authorize(_make_identity(), _make_permission())
        self.assertIsInstance(result, AuthorizationResult)
        self.assertFalse(result.allowed)

    def test_identity_invalid_type_id(self):
        with self.assertRaises(InvalidIdentityError):
            Identity(identity_id=123, username="admin")

    def test_identity_invalid_type_username(self):
        with self.assertRaises(InvalidIdentityError):
            Identity(identity_id="id-001", username=123)

    def test_role_invalid_type_id(self):
        with self.assertRaises(InvalidIdentityError):
            Role(role_id=123, role_type=RoleType.ADMIN)

    def test_permission_invalid_type_id(self):
        with self.assertRaises(InvalidIdentityError):
            Permission(permission_id=123, permission_type=PermissionType.READ)

    def test_result_invalid_type_allowed(self):
        with self.assertRaises(InvalidIdentityError):
            AuthorizationResult(allowed="yes", reason="ok")

    def test_result_invalid_type_reason(self):
        with self.assertRaises(InvalidIdentityError):
            AuthorizationResult(allowed=True, reason=123)

    def test_identity_different_ids(self):
        for iid in ["id-001", "id-002", "id-abc", "user-123"]:
            identity = _make_identity(identity_id=iid)
            self.assertEqual(identity.identity_id, iid)

    def test_role_different_ids(self):
        for rid in ["role-001", "role-002", "role-abc"]:
            role = _make_role(role_id=rid)
            self.assertEqual(role.role_id, rid)

    def test_permission_different_ids(self):
        for pid in ["perm-001", "perm-002", "perm-abc"]:
            perm = _make_permission(permission_id=pid)
            self.assertEqual(perm.permission_id, pid)

    def test_result_reason_messages(self):
        for reason in ["granted", "denied", "insufficient permissions", "expired"]:
            result = AuthorizationResult(allowed=True, reason=reason)
            self.assertEqual(result.reason, reason)

    def test_authenticate_multiple_users(self):
        class MockProvider(AuthenticationProvider):
            def authenticate(self, identity_data):
                return Identity(
                    identity_id=identity_data["id"],
                    username=identity_data["username"],
                )
        provider = MockProvider()
        for data in [
            {"id": "id-001", "username": "admin"},
            {"id": "id-002", "username": "operator"},
            {"id": "id-003", "username": "viewer"},
        ]:
            identity = provider.authenticate(data)
            self.assertEqual(identity.username, data["username"])

    def test_authorize_multiple_permissions(self):
        class MockGuard(AuthorizationGuard):
            def authorize(self, identity, permission):
                return AuthorizationResult(
                    allowed=permission.permission_type != PermissionType.ADMIN,
                    reason="checked",
                )
        guard = MockGuard()
        identity = _make_identity()
        for pt in PermissionType:
            perm = _make_permission(permission_type=pt)
            result = guard.authorize(identity, perm)
            self.assertIsInstance(result, AuthorizationResult)

    def test_role_type_admin_value(self):
        self.assertEqual(RoleType.ADMIN.value, "admin")

    def test_role_type_operator_value(self):
        self.assertEqual(RoleType.OPERATOR.value, "operator")

    def test_role_type_viewer_value(self):
        self.assertEqual(RoleType.VIEWER.value, "viewer")

    def test_permission_type_read_value(self):
        self.assertEqual(PermissionType.READ.value, "read")

    def test_permission_type_execute_value(self):
        self.assertEqual(PermissionType.EXECUTE.value, "execute")

    def test_permission_type_backup_value(self):
        self.assertEqual(PermissionType.BACKUP.value, "backup")

    def test_permission_type_restore_value(self):
        self.assertEqual(PermissionType.RESTORE.value, "restore")

    def test_permission_type_admin_value(self):
        self.assertEqual(PermissionType.ADMIN.value, "admin")

    def test_identity_no_ssh_key(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "ssh_key"))

    def test_identity_no_api_key(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "api_key"))

    def test_role_no_password(self):
        role = _make_role()
        self.assertFalse(hasattr(role, "password"))

    def test_role_no_secret(self):
        role = _make_role()
        self.assertFalse(hasattr(role, "secret"))

    def test_role_no_token(self):
        role = _make_role()
        self.assertFalse(hasattr(role, "token"))

    def test_permission_no_password(self):
        perm = _make_permission()
        self.assertFalse(hasattr(perm, "password"))

    def test_permission_no_secret(self):
        perm = _make_permission()
        self.assertFalse(hasattr(perm, "secret"))

    def test_permission_no_token(self):
        perm = _make_permission()
        self.assertFalse(hasattr(perm, "token"))

    def test_guard_multiple_calls(self):
        class MockGuard(AuthorizationGuard):
            def __init__(self):
                self.call_count = 0
            def authorize(self, identity, permission):
                self.call_count += 1
                return AuthorizationResult(
                    allowed=True, reason="granted",
                )
        guard = MockGuard()
        for i in range(5):
            guard.authorize(_make_identity(), _make_permission())
        self.assertEqual(guard.call_count, 5)

    def test_provider_multiple_calls(self):
        class MockProvider(AuthenticationProvider):
            def __init__(self):
                self.call_count = 0
            def authenticate(self, identity_data):
                self.call_count += 1
                return Identity(
                    identity_id="id-001",
                    username="admin",
                )
        provider = MockProvider()
        for i in range(5):
            provider.authenticate({})
        self.assertEqual(provider.call_count, 5)

    def test_result_allowed_true(self):
        result = _make_auth_result(allowed=True)
        self.assertTrue(result.allowed)

    def test_result_allowed_false(self):
        result = _make_auth_result(allowed=False, reason="denied")
        self.assertFalse(result.allowed)

    def test_identity_no_subprocess(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "subprocess"))

    def test_identity_no_shell(self):
        identity = _make_identity()
        self.assertFalse(hasattr(identity, "shell"))

    def test_role_no_credential(self):
        role = _make_role()
        self.assertFalse(hasattr(role, "credential"))

    def test_role_no_private_key(self):
        role = _make_role()
        self.assertFalse(hasattr(role, "private_key"))

    def test_permission_no_credential(self):
        perm = _make_permission()
        self.assertFalse(hasattr(perm, "credential"))

    def test_permission_no_private_key(self):
        perm = _make_permission()
        self.assertFalse(hasattr(perm, "private_key"))

    def test_result_no_private_key(self):
        result = _make_auth_result()
        self.assertFalse(hasattr(result, "private_key"))

    def test_result_no_ssh(self):
        result = _make_auth_result()
        self.assertFalse(hasattr(result, "ssh"))


if __name__ == "__main__":
    unittest.main()
