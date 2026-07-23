"""
WorkOps Credential Binding Tests
Sprint047: Credential Binding Layer Foundation

覆盖：
- CredentialType enum
- CredentialReference validation
- CredentialRequirement validation
- CredentialBinding validation
- CredentialBindingResolver contract
- Error model
- Security boundary
"""

import unittest

from backup_manager.credentials.binding_model import CredentialType, CredentialReference
from backup_manager.credentials.binding_requirement import CredentialRequirement
from backup_manager.credentials.binding import CredentialBinding, CredentialBindingResolver
from backup_manager.credentials.binding_errors import (
    CredentialBindingError,
    InvalidCredentialReferenceError,
    CredentialBindingConflictError,
    CredentialNotFoundError,
)


# ============================================================================
# CredentialType
# ============================================================================

class TestCredentialType(unittest.TestCase):
    """凭证类型测试"""

    def test_ssh(self):
        self.assertEqual(CredentialType.SSH.value, "ssh")

    def test_api_token(self):
        self.assertEqual(CredentialType.API_TOKEN.value, "api_token")

    def test_password(self):
        self.assertEqual(CredentialType.PASSWORD.value, "password")

    def test_three_types(self):
        self.assertEqual(len(CredentialType), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            CredentialType("nonexistent")


# ============================================================================
# CredentialReference
# ============================================================================

class TestCredentialReference(unittest.TestCase):
    """凭证引用测试"""

    def _make_ref(self, **kwargs):
        defaults = {
            "credential_id": "cred-001",
            "credential_type": CredentialType.SSH,
            "provider": "vault",
        }
        defaults.update(kwargs)
        return CredentialReference(**defaults)

    def test_valid_ref(self):
        ref = self._make_ref()
        self.assertEqual(ref.credential_id, "cred-001")
        self.assertEqual(ref.credential_type, CredentialType.SSH)
        self.assertEqual(ref.provider, "vault")

    def test_frozen(self):
        ref = self._make_ref()
        with self.assertRaises(AttributeError):
            ref.credential_id = "other"

    def test_slots(self):
        ref = self._make_ref()
        with self.assertRaises(AttributeError):
            ref.__dict__

    def test_empty_credential_id_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            self._make_ref(credential_id="")

    def test_empty_provider_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            self._make_ref(provider="")

    def test_invalid_credential_type_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            self._make_ref(credential_type="ssh")

    def test_all_credential_types(self):
        for ct in CredentialType:
            ref = self._make_ref(credential_type=ct)
            self.assertEqual(ref.credential_type, ct)

    def test_no_forbidden_fields(self):
        ref = self._make_ref()
        for attr in ["password", "secret", "token", "private_key", "credential_value", "username"]:
            self.assertFalse(hasattr(ref, attr))

    def test_repr_no_secrets(self):
        ref = self._make_ref()
        r = repr(ref)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# CredentialRequirement
# ============================================================================

class TestCredentialRequirement(unittest.TestCase):
    """凭证需求测试"""

    def test_valid_requirement(self):
        req = CredentialRequirement(
            adapter_id="ssh-linux-001",
            credential_type=CredentialType.SSH,
        )
        self.assertEqual(req.adapter_id, "ssh-linux-001")
        self.assertEqual(req.credential_type, CredentialType.SSH)
        self.assertTrue(req.required)

    def test_frozen(self):
        req = CredentialRequirement(
            adapter_id="a1", credential_type=CredentialType.SSH,
        )
        with self.assertRaises(AttributeError):
            req.adapter_id = "other"

    def test_slots(self):
        req = CredentialRequirement(
            adapter_id="a1", credential_type=CredentialType.SSH,
        )
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            CredentialRequirement(adapter_id="", credential_type=CredentialType.SSH)

    def test_invalid_credential_type_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            CredentialRequirement(adapter_id="a1", credential_type="ssh")

    def test_required_false(self):
        req = CredentialRequirement(
            adapter_id="a1", credential_type=CredentialType.SSH, required=False,
        )
        self.assertFalse(req.required)

    def test_required_must_be_bool(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            CredentialRequirement(adapter_id="a1", credential_type=CredentialType.SSH, required=1)

    def test_no_forbidden_fields(self):
        req = CredentialRequirement(
            adapter_id="a1", credential_type=CredentialType.SSH,
        )
        for attr in ["password", "secret", "token", "private_key"]:
            self.assertFalse(hasattr(req, attr))


# ============================================================================
# CredentialBinding
# ============================================================================

class TestCredentialBinding(unittest.TestCase):
    """凭证绑定测试"""

    def _make_binding(self, **kwargs):
        ref = CredentialReference(
            credential_id="cred-001",
            credential_type=CredentialType.SSH,
            provider="vault",
        )
        defaults = {"adapter_id": "ssh-linux-001", "reference": ref}
        defaults.update(kwargs)
        return CredentialBinding(**defaults)

    def test_valid_binding(self):
        binding = self._make_binding()
        self.assertEqual(binding.adapter_id, "ssh-linux-001")
        self.assertEqual(binding.reference.credential_id, "cred-001")

    def test_frozen(self):
        binding = self._make_binding()
        with self.assertRaises(AttributeError):
            binding.adapter_id = "other"

    def test_slots(self):
        binding = self._make_binding()
        with self.assertRaises(AttributeError):
            binding.__dict__

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            self._make_binding(adapter_id="")

    def test_invalid_reference_rejected(self):
        with self.assertRaises(InvalidCredentialReferenceError):
            CredentialBinding(adapter_id="a1", reference="not_a_ref")

    def test_no_forbidden_fields(self):
        binding = self._make_binding()
        for attr in ["password", "secret", "token", "private_key", "username"]:
            self.assertFalse(hasattr(binding, attr))

    def test_repr_no_secrets(self):
        binding = self._make_binding()
        r = repr(binding)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# CredentialBindingResolver Contract
# ============================================================================

class TestCredentialBindingResolverContract(unittest.TestCase):
    """绑定解析器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(CredentialBindingResolver, ABC))

    def test_has_resolve(self):
        self.assertTrue(hasattr(CredentialBindingResolver, "resolve"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            CredentialBindingResolver()

    def test_concrete_subclass(self):
        class MockResolver(CredentialBindingResolver):
            def resolve(self, adapter_id):
                return CredentialReference(
                    credential_id="cred-001",
                    credential_type=CredentialType.SSH,
                    provider="vault",
                )
        resolver = MockResolver()
        ref = resolver.resolve("a1")
        self.assertEqual(ref.credential_id, "cred-001")

    def test_missing_resolve(self):
        class BadResolver(CredentialBindingResolver):
            pass
        with self.assertRaises(TypeError):
            BadResolver()


# ============================================================================
# Error Model
# ============================================================================

class TestCredentialBindingErrors(unittest.TestCase):
    """错误模型测试"""

    def test_binding_error(self):
        with self.assertRaises(CredentialBindingError):
            raise CredentialBindingError("test")

    def test_invalid_reference_error(self):
        with self.assertRaises(CredentialBindingError):
            raise InvalidCredentialReferenceError("test")

    def test_conflict_error(self):
        exc = CredentialBindingConflictError("a1")
        self.assertIn("a1", str(exc))

    def test_not_found_error(self):
        exc = CredentialNotFoundError("c1")
        self.assertIn("c1", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (CredentialBindingError, ("test",)),
            (InvalidCredentialReferenceError, ("test",)),
            (CredentialBindingConflictError, ("a1",)),
            (CredentialNotFoundError, ("c1",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "private_key", "credential_value"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_reference_no_credentials(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.SSH, provider="vault",
        )
        for attr in ["password", "secret", "token", "private_key", "credential_value", "ssh_key_data"]:
            self.assertFalse(hasattr(ref, attr))

    def test_binding_no_credentials(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.SSH, provider="vault",
        )
        binding = CredentialBinding(adapter_id="a1", reference=ref)
        for attr in ["password", "secret", "token", "private_key", "username"]:
            self.assertFalse(hasattr(binding, attr))

    def test_requirement_no_credentials(self):
        req = CredentialRequirement(adapter_id="a1", credential_type=CredentialType.SSH)
        for attr in ["password", "secret", "token", "private_key", "credential_value"]:
            self.assertFalse(hasattr(req, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["binding_model.py", "binding_requirement.py", "binding.py", "binding_errors.py"]:
            filepath = os.path.join("backup_manager", "credentials", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

    def test_resolver_lifecycle(self):
        """完整解析器生命周期"""
        class MockResolver(CredentialBindingResolver):
            def resolve(self, adapter_id):
                return CredentialReference(
                    credential_id="cred-001",
                    credential_type=CredentialType.SSH,
                    provider="vault",
                )
        resolver = MockResolver()
        ref = resolver.resolve("a1")
        binding = CredentialBinding(adapter_id="a1", reference=ref)
        self.assertEqual(binding.reference.credential_id, "cred-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestCredentialBindingExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidCredentialReferenceError, CredentialBindingError))
        self.assertTrue(issubclass(CredentialBindingConflictError, CredentialBindingError))
        self.assertTrue(issubclass(CredentialNotFoundError, CredentialBindingError))

    def test_reference_all_types(self):
        for ct in CredentialType:
            ref = CredentialReference(
                credential_id=f"c-{ct.value}", credential_type=ct, provider="vault",
            )
            self.assertEqual(ref.credential_type, ct)

    def test_requirement_all_types(self):
        for ct in CredentialType:
            req = CredentialRequirement(adapter_id="a1", credential_type=ct)
            self.assertEqual(req.credential_type, ct)

    def test_binding_with_api_token(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.API_TOKEN, provider="vault",
        )
        binding = CredentialBinding(adapter_id="a1", reference=ref)
        self.assertEqual(binding.reference.credential_type, CredentialType.API_TOKEN)

    def test_binding_with_password(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.PASSWORD, provider="vault",
        )
        binding = CredentialBinding(adapter_id="a1", reference=ref)
        self.assertEqual(binding.reference.credential_type, CredentialType.PASSWORD)

    def test_error_messages_safe(self):
        try:
            raise CredentialBindingError("test")
        except CredentialBindingError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_reference_repr_no_secrets(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.SSH, provider="vault",
        )
        r = repr(ref)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())

    def test_requirement_repr_no_secrets(self):
        req = CredentialRequirement(adapter_id="a1", credential_type=CredentialType.SSH)
        r = repr(req)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())

    def test_binding_repr_no_secrets(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.SSH, provider="vault",
        )
        binding = CredentialBinding(adapter_id="a1", reference=ref)
        r = repr(binding)
        for term in ["password", "secret", "token", "private_key"]:
            self.assertNotIn(term, r.lower())

    def test_resolver_returns_reference(self):
        class MockResolver(CredentialBindingResolver):
            def resolve(self, adapter_id):
                return CredentialReference(
                    credential_id="c1", credential_type=CredentialType.SSH, provider="vault",
                )
        resolver = MockResolver()
        ref = resolver.resolve("a1")
        self.assertIsInstance(ref, CredentialReference)

    def test_reference_provider_types(self):
        for provider in ["vault", "aws-secrets", "env", "file"]:
            ref = CredentialReference(
                credential_id="c1", credential_type=CredentialType.SSH, provider=provider,
            )
            self.assertEqual(ref.provider, provider)

    def test_binding_preserves_reference(self):
        ref = CredentialReference(
            credential_id="c1", credential_type=CredentialType.API_TOKEN, provider="vault",
        )
        binding = CredentialBinding(adapter_id="a1", reference=ref)
        self.assertIs(binding.reference, ref)

    def test_requirement_default_required(self):
        req = CredentialRequirement(adapter_id="a1", credential_type=CredentialType.SSH)
        self.assertTrue(req.required)

    def test_requirement_not_required(self):
        req = CredentialRequirement(adapter_id="a1", credential_type=CredentialType.SSH, required=False)
        self.assertFalse(req.required)

    def test_conflict_error_message(self):
        exc = CredentialBindingConflictError("test-adapter")
        self.assertIn("test-adapter", str(exc))

    def test_not_found_error_message(self):
        exc = CredentialNotFoundError("test-cred")
        self.assertIn("test-cred", str(exc))


if __name__ == "__main__":
    unittest.main()
