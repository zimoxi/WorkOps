"""
WorkOps Adapter Integration Tests
Sprint046: Device Adapter Integration Foundation

覆盖：
- AdapterType enum
- AdapterDescriptor validation
- AdapterProvider contract
- AdapterRegistry
- AdapterIntegration model
- Error model
- Security boundary
"""

import unittest

from backup_manager.devices.capability import DeviceCapability, DeviceType
from backup_manager.adapters.adapter_model import AdapterType
from backup_manager.adapters.adapter_descriptor import AdapterDescriptor
from backup_manager.adapters.adapter_provider import AdapterProvider
from backup_manager.adapters.adapter_registry import AdapterIntegrationRegistry
from backup_manager.adapters.adapter_integration import AdapterIntegration
from backup_manager.adapters.adapter_errors import (
    AdapterIntegrationError,
    InvalidAdapterError,
    AdapterConflictError,
    AdapterNotFoundError,
)


# ============================================================================
# AdapterType
# ============================================================================

class TestAdapterType(unittest.TestCase):
    """适配器类型测试"""

    def test_linux(self):
        self.assertEqual(AdapterType.LINUX.value, "linux")

    def test_pve(self):
        self.assertEqual(AdapterType.PVE.value, "pve")

    def test_omv(self):
        self.assertEqual(AdapterType.OMV.value, "omv")

    def test_nas(self):
        self.assertEqual(AdapterType.NAS.value, "nas")

    def test_four_types(self):
        self.assertEqual(len(AdapterType), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            AdapterType("nonexistent")


# ============================================================================
# AdapterDescriptor
# ============================================================================

class TestAdapterDescriptor(unittest.TestCase):
    """适配器描述符测试"""

    def _make_descriptor(self, **kwargs):
        defaults = {
            "adapter_id": "ssh-linux-001",
            "adapter_type": AdapterType.LINUX,
            "capabilities": (DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
            "version": "1.0.0",
        }
        defaults.update(kwargs)
        return AdapterDescriptor(**defaults)

    def test_valid_descriptor(self):
        desc = self._make_descriptor()
        self.assertEqual(desc.adapter_id, "ssh-linux-001")
        self.assertEqual(desc.adapter_type, AdapterType.LINUX)
        self.assertEqual(desc.version, "1.0.0")

    def test_frozen(self):
        desc = self._make_descriptor()
        with self.assertRaises(AttributeError):
            desc.adapter_id = "other"

    def test_slots(self):
        desc = self._make_descriptor()
        with self.assertRaises(AttributeError):
            desc.__dict__

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            self._make_descriptor(adapter_id="")

    def test_empty_version_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            self._make_descriptor(version="")

    def test_invalid_adapter_type_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            self._make_descriptor(adapter_type="linux")

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(InvalidAdapterError):
            self._make_descriptor(capabilities=[DeviceCapability.STATUS_QUERY])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            self._make_descriptor(capabilities=("bad",))

    def test_empty_capabilities_allowed(self):
        desc = self._make_descriptor(capabilities=())
        self.assertEqual(len(desc.capabilities), 0)

    def test_multiple_capabilities(self):
        desc = self._make_descriptor(capabilities=(
            DeviceCapability.STATUS_QUERY,
            DeviceCapability.SYSTEM_INFO,
            DeviceCapability.STORAGE_QUERY,
        ))
        self.assertEqual(len(desc.capabilities), 3)

    def test_no_forbidden_fields(self):
        desc = self._make_descriptor()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "command", "connection_string"]:
            self.assertFalse(hasattr(desc, attr))


# ============================================================================
# AdapterProvider Contract
# ============================================================================

class TestAdapterProviderContract(unittest.TestCase):
    """适配器提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AdapterProvider, ABC))

    def test_has_descriptor(self):
        self.assertTrue(hasattr(AdapterProvider, "descriptor"))

    def test_has_supports(self):
        self.assertTrue(hasattr(AdapterProvider, "supports"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AdapterProvider()

    def test_concrete_subclass(self):
        class MockProvider(AdapterProvider):
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id="mock-001",
                    adapter_type=AdapterType.LINUX,
                    capabilities=(DeviceCapability.STATUS_QUERY,),
                    version="1.0.0",
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
        provider = MockProvider()
        self.assertEqual(provider.descriptor().adapter_id, "mock-001")
        self.assertTrue(provider.supports(DeviceCapability.STATUS_QUERY))
        self.assertFalse(provider.supports(DeviceCapability.BACKUP_SOURCE))

    def test_missing_descriptor(self):
        class BadProvider(AdapterProvider):
            def supports(self, capability):
                return False
        with self.assertRaises(TypeError):
            BadProvider()

    def test_missing_supports(self):
        class BadProvider(AdapterProvider):
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id="bad", adapter_type=AdapterType.LINUX,
                    capabilities=(), version="1.0.0",
                )
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# AdapterIntegrationRegistry
# ============================================================================

class TestAdapterIntegrationRegistry(unittest.TestCase):
    """适配器注册表测试"""

    def setUp(self):
        self.registry = AdapterIntegrationRegistry()

    def _make_provider(self, adapter_id="mock-001", caps=(DeviceCapability.STATUS_QUERY,)):
        class MockProvider(AdapterProvider):
            def __init__(self, aid, c):
                self._id = aid
                self._caps = c
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id=self._id,
                    adapter_type=AdapterType.LINUX,
                    capabilities=self._caps,
                    version="1.0.0",
                )
            def supports(self, capability):
                return capability in self._caps
        return MockProvider(adapter_id, caps)

    def test_register_and_get(self):
        provider = self._make_provider()
        self.registry.register(provider)
        got = self.registry.get("mock-001")
        self.assertIs(got, provider)

    def test_duplicate_rejected(self):
        provider = self._make_provider()
        self.registry.register(provider)
        with self.assertRaises(AdapterConflictError):
            self.registry.register(self._make_provider())

    def test_get_not_found(self):
        with self.assertRaises(AdapterNotFoundError):
            self.registry.get("nonexistent")

    def test_list(self):
        self.registry.register(self._make_provider("a1"))
        self.registry.register(self._make_provider("a2"))
        types = self.registry.list()
        self.assertEqual(len(types), 2)
        self.assertIn("a1", types)
        self.assertIn("a2", types)

    def test_supports(self):
        self.registry.register(self._make_provider("a1", (DeviceCapability.STATUS_QUERY,)))
        self.registry.register(self._make_provider("a2", (DeviceCapability.STORAGE_QUERY,)))
        result = self.registry.supports(DeviceCapability.STATUS_QUERY)
        self.assertEqual(result, ["a1"])

    def test_supports_empty(self):
        self.assertEqual(self.registry.supports(DeviceCapability.STATUS_QUERY), [])

    def test_non_provider_rejected(self):
        with self.assertRaises(TypeError):
            self.registry.register("not_a_provider")

    def test_no_dynamic_loading(self):
        import ast
        with open("backup_manager/adapters/adapter_registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("__import__", "import_module"):
                    self.fail("registry uses dynamic import")


# ============================================================================
# AdapterIntegration
# ============================================================================

class TestAdapterIntegration(unittest.TestCase):
    """适配器集成模型测试"""

    def test_valid_integration(self):
        integration = AdapterIntegration(
            adapter_id="ssh-linux-001",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        self.assertEqual(integration.adapter_id, "ssh-linux-001")
        self.assertEqual(integration.device_type, DeviceType.SERVER)

    def test_frozen(self):
        integration = AdapterIntegration(
            adapter_id="a1", device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        with self.assertRaises(AttributeError):
            integration.adapter_id = "other"

    def test_slots(self):
        integration = AdapterIntegration(
            adapter_id="a1", device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        with self.assertRaises(AttributeError):
            integration.__dict__

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            AdapterIntegration(adapter_id="", device_type=DeviceType.SERVER, capabilities=())

    def test_invalid_device_type_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            AdapterIntegration(adapter_id="a1", device_type="server", capabilities=())

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(InvalidAdapterError):
            AdapterIntegration(adapter_id="a1", device_type=DeviceType.SERVER, capabilities=[])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(InvalidAdapterError):
            AdapterIntegration(adapter_id="a1", device_type=DeviceType.SERVER, capabilities=("bad",))

    def test_no_forbidden_fields(self):
        integration = AdapterIntegration(
            adapter_id="a1", device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(integration, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestAdapterIntegrationErrors(unittest.TestCase):
    """错误模型测试"""

    def test_integration_error(self):
        with self.assertRaises(AdapterIntegrationError):
            raise AdapterIntegrationError("test")

    def test_invalid_adapter_error(self):
        with self.assertRaises(AdapterIntegrationError):
            raise InvalidAdapterError("test")

    def test_conflict_error(self):
        exc = AdapterConflictError("a1")
        self.assertIn("a1", str(exc))

    def test_not_found_error(self):
        exc = AdapterNotFoundError("a1")
        self.assertIn("a1", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (AdapterIntegrationError, ("test",)),
            (InvalidAdapterError, ("test",)),
            (AdapterConflictError, ("a1",)),
            (AdapterNotFoundError, ("a1",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_descriptor_no_credentials(self):
        desc = AdapterDescriptor(
            adapter_id="a1", adapter_type=AdapterType.LINUX,
            capabilities=(DeviceCapability.STATUS_QUERY,), version="1.0.0",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(desc, attr))

    def test_integration_no_credentials(self):
        integration = AdapterIntegration(
            adapter_id="a1", device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(integration, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["adapter_model.py", "adapter_descriptor.py", "adapter_provider.py",
                         "adapter_registry.py", "adapter_integration.py", "adapter_errors.py"]:
            filepath = os.path.join("backup_manager", "adapters", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

    def test_registry_lifecycle(self):
        """完整注册表生命周期"""
        class MockProvider(AdapterProvider):
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id="a1", adapter_type=AdapterType.LINUX,
                    capabilities=(DeviceCapability.STATUS_QUERY,), version="1.0.0",
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
        registry = AdapterIntegrationRegistry()
        registry.register(MockProvider())
        self.assertTrue(len(registry.list()) == 1)
        self.assertTrue(len(registry.supports(DeviceCapability.STATUS_QUERY)) == 1)


# ============================================================================
# Extended Tests
# ============================================================================

class TestAdapterIntegrationExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidAdapterError, AdapterIntegrationError))
        self.assertTrue(issubclass(AdapterConflictError, AdapterIntegrationError))
        self.assertTrue(issubclass(AdapterNotFoundError, AdapterIntegrationError))

    def test_descriptor_repr_no_secrets(self):
        desc = AdapterDescriptor(
            adapter_id="a1", adapter_type=AdapterType.LINUX,
            capabilities=(DeviceCapability.STATUS_QUERY,), version="1.0.0",
        )
        r = repr(desc)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_integration_repr_no_secrets(self):
        integration = AdapterIntegration(
            adapter_id="a1", device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        r = repr(integration)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_registry_supports_multiple(self):
        class MockProvider(AdapterProvider):
            def __init__(self, aid, caps):
                self._id = aid
                self._caps = caps
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id=self._id, adapter_type=AdapterType.LINUX,
                    capabilities=self._caps, version="1.0.0",
                )
            def supports(self, capability):
                return capability in self._caps
        registry = AdapterIntegrationRegistry()
        registry.register(MockProvider("a1", (DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO)))
        registry.register(MockProvider("a2", (DeviceCapability.STATUS_QUERY, DeviceCapability.STORAGE_QUERY)))
        result = registry.supports(DeviceCapability.STATUS_QUERY)
        self.assertEqual(len(result), 2)

    def test_descriptor_all_adapter_types(self):
        for at in AdapterType:
            desc = AdapterDescriptor(
                adapter_id=f"a-{at.value}", adapter_type=at,
                capabilities=(DeviceCapability.STATUS_QUERY,), version="1.0.0",
            )
            self.assertEqual(desc.adapter_type, at)

    def test_integration_all_device_types(self):
        for dt in DeviceType:
            integration = AdapterIntegration(
                adapter_id=f"a-{dt.value}", device_type=dt,
                capabilities=(DeviceCapability.STATUS_QUERY,),
            )
            self.assertEqual(integration.device_type, dt)

    def test_registry_list_empty(self):
        registry = AdapterIntegrationRegistry()
        self.assertEqual(registry.list(), [])

    def test_registry_get_returns_same(self):
        class MockProvider(AdapterProvider):
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id="a1", adapter_type=AdapterType.LINUX,
                    capabilities=(DeviceCapability.STATUS_QUERY,), version="1.0.0",
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
        registry = AdapterIntegrationRegistry()
        provider = MockProvider()
        registry.register(provider)
        self.assertIs(registry.get("a1"), provider)

    def test_provider_supports_false(self):
        class MockProvider(AdapterProvider):
            def descriptor(self):
                return AdapterDescriptor(
                    adapter_id="a1", adapter_type=AdapterType.LINUX,
                    capabilities=(), version="1.0.0",
                )
            def supports(self, capability):
                return False
        provider = MockProvider()
        self.assertFalse(provider.supports(DeviceCapability.STATUS_QUERY))

    def test_descriptor_no_connection_string(self):
        desc = AdapterDescriptor(
            adapter_id="a1", adapter_type=AdapterType.LINUX,
            capabilities=(DeviceCapability.STATUS_QUERY,), version="1.0.0",
        )
        self.assertFalse(hasattr(desc, "connection_string"))

    def test_error_messages_safe(self):
        try:
            raise AdapterIntegrationError("test")
        except AdapterIntegrationError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())


if __name__ == "__main__":
    unittest.main()
