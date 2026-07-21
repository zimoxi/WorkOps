"""
WorkOps Adapter Capability Registry Tests
Sprint026: Adapter Capability Registry

覆盖：
- AdapterCapabilityDeclaration
- AdapterCapabilityRegistry
- AdapterCapabilityProvider contract
- Security boundary
"""

import unittest

from backup_manager.devices.capability import DeviceCapability, DeviceType
from backup_manager.adapters.capability import AdapterCapabilityDeclaration
from backup_manager.adapters.capability_registry import AdapterCapabilityRegistry
from backup_manager.adapters.contracts import AdapterCapabilityProvider
from backup_manager.adapters.errors import (
    AdapterCapabilityError,
    AdapterAlreadyExistsError,
    AdapterNotFoundError,
    CapabilityNotSupportedError,
)


# ============================================================================
# AdapterCapabilityDeclaration
# ============================================================================

class TestAdapterCapabilityDeclaration(unittest.TestCase):
    """能力声明测试"""

    def test_valid_declaration(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
        )
        self.assertEqual(decl.adapter_type, "ssh_readonly")
        self.assertIn(DeviceCapability.STATUS_QUERY, decl.capabilities)

    def test_frozen(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        with self.assertRaises(AttributeError):
            decl.adapter_type = "other"

    def test_slots(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        with self.assertRaises(AttributeError):
            decl.__dict__

    def test_empty_adapter_type_rejected(self):
        with self.assertRaises(AdapterCapabilityError):
            AdapterCapabilityDeclaration(
                adapter_type="",
                capabilities=(DeviceCapability.STATUS_QUERY,),
            )

    def test_whitespace_adapter_type_rejected(self):
        with self.assertRaises(AdapterCapabilityError):
            AdapterCapabilityDeclaration(
                adapter_type="   ",
                capabilities=(DeviceCapability.STATUS_QUERY,),
            )

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(AdapterCapabilityError):
            AdapterCapabilityDeclaration(
                adapter_type="ssh_readonly",
                capabilities=[DeviceCapability.STATUS_QUERY],
            )

    def test_invalid_capability_rejected(self):
        with self.assertRaises(AdapterCapabilityError):
            AdapterCapabilityDeclaration(
                adapter_type="ssh_readonly",
                capabilities=("bad_cap",),
            )

    def test_empty_capabilities_allowed(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(),
        )
        self.assertEqual(len(decl.capabilities), 0)

    def test_multiple_capabilities(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(
                DeviceCapability.STATUS_QUERY,
                DeviceCapability.SYSTEM_INFO,
                DeviceCapability.STORAGE_QUERY,
            ),
        )
        self.assertEqual(len(decl.capabilities), 3)

    def test_no_forbidden_fields(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        for field in ["password", "credential", "secret", "token", "command", "endpoint"]:
            self.assertFalse(hasattr(decl, field))

    def test_repr_no_secrets(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        r = repr(decl)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# AdapterCapabilityRegistry
# ============================================================================

class TestAdapterCapabilityRegistry(unittest.TestCase):
    """能力注册表测试"""

    def setUp(self):
        self.registry = AdapterCapabilityRegistry()
        self.decl = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
        )

    def test_register_and_get(self):
        self.registry.register(self.decl)
        got = self.registry.get("ssh_readonly")
        self.assertEqual(got.adapter_type, "ssh_readonly")

    def test_duplicate_rejected(self):
        self.registry.register(self.decl)
        with self.assertRaises(AdapterAlreadyExistsError):
            self.registry.register(self.decl)

    def test_get_not_found(self):
        with self.assertRaises(AdapterNotFoundError):
            self.registry.get("nonexistent")

    def test_list(self):
        self.registry.register(self.decl)
        decl2 = AdapterCapabilityDeclaration(
            adapter_type="mock",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        self.registry.register(decl2)
        types = self.registry.list()
        self.assertEqual(len(types), 2)
        self.assertIn("ssh_readonly", types)
        self.assertIn("mock", types)

    def test_supports_true(self):
        self.registry.register(self.decl)
        self.assertTrue(
            self.registry.supports("ssh_readonly", DeviceCapability.STATUS_QUERY)
        )

    def test_supports_false(self):
        self.registry.register(self.decl)
        self.assertFalse(
            self.registry.supports("ssh_readonly", DeviceCapability.BACKUP_SOURCE)
        )

    def test_supports_unregistered(self):
        self.assertFalse(
            self.registry.supports("nonexistent", DeviceCapability.STATUS_QUERY)
        )

    def test_register_non_declaration_rejected(self):
        with self.assertRaises(TypeError):
            self.registry.register("not_a_declaration")

    def test_no_dynamic_loading(self):
        import ast
        with open("backup_manager/adapters/capability_registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("__import__", "import_module"):
                    self.fail("registry uses dynamic import")

    def test_no_connection_logic(self):
        """确认注册表没有连接逻辑"""
        import ast
        with open("backup_manager/adapters/capability_registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name in ("connect", "execute", "scan"):
                    self.fail(f"forbidden method {node.name} in registry")

    def test_supports_all_capabilities(self):
        """注册所有能力后逐一检查"""
        all_caps = tuple(DeviceCapability)
        self.registry.register(AdapterCapabilityDeclaration(
            adapter_type="full",
            capabilities=all_caps,
        ))
        for cap in DeviceCapability:
            self.assertTrue(self.registry.supports("full", cap))

    def test_empty_capabilities_supports_nothing(self):
        self.registry.register(AdapterCapabilityDeclaration(
            adapter_type="empty",
            capabilities=(),
        ))
        for cap in DeviceCapability:
            self.assertFalse(self.registry.supports("empty", cap))

    def test_multiple_registrations_independent(self):
        self.registry.register(self.decl)
        decl2 = AdapterCapabilityDeclaration(
            adapter_type="mock",
            capabilities=(DeviceCapability.BACKUP_TARGET,),
        )
        self.registry.register(decl2)
        self.assertTrue(self.registry.supports("mock", DeviceCapability.BACKUP_TARGET))
        self.assertFalse(self.registry.supports("mock", DeviceCapability.STATUS_QUERY))

    def test_get_returns_same_declaration(self):
        self.registry.register(self.decl)
        got = self.registry.get("ssh_readonly")
        self.assertIs(got, self.decl)

    def test_list_empty(self):
        self.assertEqual(self.registry.list(), [])


# ============================================================================
# AdapterCapabilityProvider Contract
# ============================================================================

class TestAdapterCapabilityProvider(unittest.TestCase):
    """能力提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AdapterCapabilityProvider, ABC))

    def test_has_abstract_methods(self):
        self.assertTrue(hasattr(AdapterCapabilityProvider, "adapter_type"))
        self.assertTrue(hasattr(AdapterCapabilityProvider, "supported_capabilities"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AdapterCapabilityProvider()

    def test_concrete_subclass(self):
        """具体子类可以实例化"""
        class MockProvider(AdapterCapabilityProvider):
            @property
            def adapter_type(self):
                return "mock"
            @property
            def supported_capabilities(self):
                return (DeviceCapability.STATUS_QUERY,)
        provider = MockProvider()
        self.assertEqual(provider.adapter_type, "mock")
        self.assertIn(DeviceCapability.STATUS_QUERY, provider.supported_capabilities)

    def test_missing_adapter_type(self):
        """缺少 adapter_type 不能实例化"""
        class BadProvider(AdapterCapabilityProvider):
            @property
            def supported_capabilities(self):
                return ()
        with self.assertRaises(TypeError):
            BadProvider()

    def test_missing_capabilities(self):
        """缺少 supported_capabilities 不能实例化"""
        class BadProvider(AdapterCapabilityProvider):
            @property
            def adapter_type(self):
                return "bad"
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_error_messages_no_secrets(self):
        """错误消息不泄漏 secret"""
        for exc_cls, args in [
            (AdapterAlreadyExistsError, ("test",)),
            (AdapterNotFoundError, ("test",)),
            (CapabilityNotSupportedError, ("test", "cap")),
            (AdapterCapabilityError, ("test",)),
        ]:
            try:
                raise exc_cls(*args)
            except Exception as e:
                msg = str(e)
                self.assertNotIn("password", msg.lower())
                self.assertNotIn("secret", msg.lower())
                self.assertNotIn("credential", msg.lower())
                self.assertNotIn("token", msg.lower())

    def test_registry_no_secrets(self):
        registry = AdapterCapabilityRegistry()
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(registry, attr))

    def test_declaration_no_secrets(self):
        decl = AdapterCapabilityDeclaration(
            adapter_type="test",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        for attr in ["password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(decl, attr))

    def test_no_subprocess(self):
        import ast
        import os
        adapters_dir = os.path.join("backup_manager", "adapters")
        for filename in ["capability.py", "capability_registry.py", "contracts.py"]:
            filepath = os.path.join(adapters_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

    def test_no_command_execution(self):
        import ast
        for filename in ["capability.py", "capability_registry.py", "contracts.py"]:
            filepath = f"backup_manager/adapters/{filename}"
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() found in {filename}")

    def test_contract_no_secrets(self):
        """契约接口不泄漏 secret"""
        r = repr(AdapterCapabilityProvider)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_full_registry_lifecycle(self):
        """完整注册表生命周期"""
        registry = AdapterCapabilityRegistry()
        decl1 = AdapterCapabilityDeclaration(
            adapter_type="ssh_readonly",
            capabilities=(DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
        )
        decl2 = AdapterCapabilityDeclaration(
            adapter_type="mock",
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        registry.register(decl1)
        registry.register(decl2)
        self.assertEqual(len(registry.list()), 2)
        self.assertTrue(registry.supports("ssh_readonly", DeviceCapability.SYSTEM_INFO))
        self.assertFalse(registry.supports("mock", DeviceCapability.SYSTEM_INFO))
        got = registry.get("ssh_readonly")
        self.assertIs(got, decl1)

    def test_all_device_capabilities_declarable(self):
        """所有 DeviceCapability 都可以声明"""
        all_caps = tuple(DeviceCapability)
        decl = AdapterCapabilityDeclaration(
            adapter_type="full",
            capabilities=all_caps,
        )
        self.assertEqual(len(decl.capabilities), len(DeviceCapability))


if __name__ == "__main__":
    unittest.main()
