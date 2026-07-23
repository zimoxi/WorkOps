"""
WorkOps Linux Adapter Tests
Sprint048: Linux Adapter v1 Foundation

覆盖：
- LinuxCapability enum
- LinuxOperation enum
- LinuxAdapterDescriptor validation
- LinuxAdapterProvider contract
- LinuxCapabilityMapping validation
- Error model
- Security boundary
"""

import unittest

from backup_manager.adapters.linux.capability import LinuxCapability, LinuxOperation
from backup_manager.adapters.linux.model import LinuxAdapterDescriptor
from backup_manager.adapters.linux.provider import LinuxAdapterProvider
from backup_manager.adapters.linux.capability_mapping import LinuxCapabilityMapping
from backup_manager.adapters.linux.errors import (
    LinuxAdapterError,
    InvalidLinuxAdapterError,
    LinuxCapabilityError,
    LinuxOperationError,
)
from backup_manager.devices.capability import DeviceCapability


# ============================================================================
# LinuxCapability
# ============================================================================

class TestLinuxCapability(unittest.TestCase):
    """Linux 能力测试"""

    def test_system_info(self):
        self.assertEqual(LinuxCapability.SYSTEM_INFO.value, "system_info")

    def test_storage_info(self):
        self.assertEqual(LinuxCapability.STORAGE_INFO.value, "storage_info")

    def test_network_info(self):
        self.assertEqual(LinuxCapability.NETWORK_INFO.value, "network_info")

    def test_service_status(self):
        self.assertEqual(LinuxCapability.SERVICE_STATUS.value, "service_status")

    def test_four_capabilities(self):
        self.assertEqual(len(LinuxCapability), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            LinuxCapability("nonexistent")


# ============================================================================
# LinuxOperation
# ============================================================================

class TestLinuxOperation(unittest.TestCase):
    """Linux 操作测试"""

    def test_query_system(self):
        self.assertEqual(LinuxOperation.QUERY_SYSTEM.value, "query_system")

    def test_query_storage(self):
        self.assertEqual(LinuxOperation.QUERY_STORAGE.value, "query_storage")

    def test_query_network(self):
        self.assertEqual(LinuxOperation.QUERY_NETWORK.value, "query_network")

    def test_query_service(self):
        self.assertEqual(LinuxOperation.QUERY_SERVICE.value, "query_service")

    def test_four_operations(self):
        self.assertEqual(len(LinuxOperation), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            LinuxOperation("nonexistent")


# ============================================================================
# LinuxAdapterDescriptor
# ============================================================================

class TestLinuxAdapterDescriptor(unittest.TestCase):
    """Linux 适配器描述符测试"""

    def _make_descriptor(self, **kwargs):
        defaults = {
            "adapter_id": "linux-001",
            "version": "1.0.0",
            "capabilities": (LinuxCapability.SYSTEM_INFO, LinuxCapability.STORAGE_INFO),
        }
        defaults.update(kwargs)
        return LinuxAdapterDescriptor(**defaults)

    def test_valid_descriptor(self):
        desc = self._make_descriptor()
        self.assertEqual(desc.adapter_id, "linux-001")
        self.assertEqual(desc.version, "1.0.0")
        self.assertEqual(len(desc.capabilities), 2)

    def test_frozen(self):
        desc = self._make_descriptor()
        with self.assertRaises(AttributeError):
            desc.adapter_id = "other"

    def test_slots(self):
        desc = self._make_descriptor()
        with self.assertRaises(AttributeError):
            desc.__dict__

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            self._make_descriptor(adapter_id="")

    def test_empty_version_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            self._make_descriptor(version="")

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            self._make_descriptor(capabilities=[LinuxCapability.SYSTEM_INFO])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            self._make_descriptor(capabilities=("bad",))

    def test_empty_capabilities_allowed(self):
        desc = self._make_descriptor(capabilities=())
        self.assertEqual(len(desc.capabilities), 0)

    def test_multiple_capabilities(self):
        desc = self._make_descriptor(capabilities=(
            LinuxCapability.SYSTEM_INFO,
            LinuxCapability.STORAGE_INFO,
            LinuxCapability.NETWORK_INFO,
            LinuxCapability.SERVICE_STATUS,
        ))
        self.assertEqual(len(desc.capabilities), 4)

    def test_no_forbidden_fields(self):
        desc = self._make_descriptor()
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "ip", "hostname"]:
            self.assertFalse(hasattr(desc, attr))


# ============================================================================
# LinuxAdapterProvider Contract
# ============================================================================

class TestLinuxAdapterProviderContract(unittest.TestCase):
    """Linux 适配器提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(LinuxAdapterProvider, ABC))

    def test_has_descriptor(self):
        self.assertTrue(hasattr(LinuxAdapterProvider, "descriptor"))

    def test_has_supports(self):
        self.assertTrue(hasattr(LinuxAdapterProvider, "supports"))

    def test_has_execute(self):
        self.assertTrue(hasattr(LinuxAdapterProvider, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            LinuxAdapterProvider()

    def test_concrete_subclass(self):
        class MockProvider(LinuxAdapterProvider):
            def descriptor(self):
                return LinuxAdapterDescriptor(
                    adapter_id="linux-001", version="1.0.0",
                    capabilities=(LinuxCapability.SYSTEM_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        self.assertEqual(provider.descriptor().adapter_id, "linux-001")
        self.assertTrue(provider.supports(LinuxCapability.SYSTEM_INFO))
        self.assertFalse(provider.supports(LinuxCapability.STORAGE_INFO))
        result = provider.execute(LinuxOperation.QUERY_SYSTEM)
        self.assertEqual(result["status"], "ok")

    def test_missing_descriptor(self):
        class BadProvider(LinuxAdapterProvider):
            def supports(self, capability):
                return False
            def execute(self, operation):
                pass
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# LinuxCapabilityMapping
# ============================================================================

class TestLinuxCapabilityMapping(unittest.TestCase):
    """Linux 能力映射测试"""

    def test_valid_mapping(self):
        mapping = LinuxCapabilityMapping(
            linux_capability=LinuxCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        self.assertEqual(mapping.linux_capability, LinuxCapability.SYSTEM_INFO)
        self.assertEqual(mapping.device_capability, DeviceCapability.SYSTEM_INFO)

    def test_frozen(self):
        mapping = LinuxCapabilityMapping(
            linux_capability=LinuxCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        with self.assertRaises(AttributeError):
            mapping.linux_capability = LinuxCapability.STORAGE_INFO

    def test_slots(self):
        mapping = LinuxCapabilityMapping(
            linux_capability=LinuxCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        with self.assertRaises(AttributeError):
            mapping.__dict__

    def test_invalid_linux_capability_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            LinuxCapabilityMapping(
                linux_capability="system_info",
                device_capability=DeviceCapability.SYSTEM_INFO,
            )

    def test_invalid_device_capability_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            LinuxCapabilityMapping(
                linux_capability=LinuxCapability.SYSTEM_INFO,
                device_capability="system_info",
            )

    def test_storage_mapping(self):
        mapping = LinuxCapabilityMapping(
            linux_capability=LinuxCapability.STORAGE_INFO,
            device_capability=DeviceCapability.STORAGE_QUERY,
        )
        self.assertEqual(mapping.linux_capability, LinuxCapability.STORAGE_INFO)


# ============================================================================
# Error Model
# ============================================================================

class TestLinuxAdapterErrors(unittest.TestCase):
    """错误模型测试"""

    def test_adapter_error(self):
        with self.assertRaises(LinuxAdapterError):
            raise LinuxAdapterError("test")

    def test_invalid_adapter_error(self):
        with self.assertRaises(LinuxAdapterError):
            raise InvalidLinuxAdapterError("test")

    def test_capability_error(self):
        with self.assertRaises(LinuxAdapterError):
            raise LinuxCapabilityError("test")

    def test_operation_error(self):
        with self.assertRaises(LinuxAdapterError):
            raise LinuxOperationError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (LinuxAdapterError, ("test",)),
            (InvalidLinuxAdapterError, ("test",)),
            (LinuxCapabilityError, ("test",)),
            (LinuxOperationError, ("test",)),
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
        desc = LinuxAdapterDescriptor(
            adapter_id="linux-001", version="1.0.0",
            capabilities=(LinuxCapability.SYSTEM_INFO,),
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(desc, attr))

    def test_no_subprocess(self):
        import ast
        import os
        linux_dir = os.path.join("backup_manager", "adapters", "linux")
        for filename in os.listdir(linux_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(linux_dir, filename)
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
        linux_dir = os.path.join("backup_manager", "adapters", "linux")
        for filename in os.listdir(linux_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(linux_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_provider_lifecycle(self):
        """完整提供者生命周期"""
        class MockProvider(LinuxAdapterProvider):
            def descriptor(self):
                return LinuxAdapterDescriptor(
                    adapter_id="linux-001", version="1.0.0",
                    capabilities=(LinuxCapability.SYSTEM_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        desc = provider.descriptor()
        self.assertEqual(desc.adapter_id, "linux-001")
        self.assertTrue(provider.supports(LinuxCapability.SYSTEM_INFO))
        result = provider.execute(LinuxOperation.QUERY_SYSTEM)
        self.assertEqual(result["status"], "ok")


# ============================================================================
# Extended Tests
# ============================================================================

class TestLinuxAdapterExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidLinuxAdapterError, LinuxAdapterError))
        self.assertTrue(issubclass(LinuxCapabilityError, LinuxAdapterError))
        self.assertTrue(issubclass(LinuxOperationError, LinuxAdapterError))

    def test_descriptor_repr_no_secrets(self):
        desc = LinuxAdapterDescriptor(
            adapter_id="linux-001", version="1.0.0",
            capabilities=(LinuxCapability.SYSTEM_INFO,),
        )
        r = repr(desc)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_mapping_repr_no_secrets(self):
        mapping = LinuxCapabilityMapping(
            linux_capability=LinuxCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        r = repr(mapping)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_all_capabilities(self):
        for cap in LinuxCapability:
            desc = LinuxAdapterDescriptor(
                adapter_id="linux-001", version="1.0.0",
                capabilities=(cap,),
            )
            self.assertIn(cap, desc.capabilities)

    def test_all_operations(self):
        for op in LinuxOperation:
            self.assertIsInstance(op.value, str)

    def test_descriptor_all_capabilities(self):
        for cap in LinuxCapability:
            desc = LinuxAdapterDescriptor(
                adapter_id="linux-001", version="1.0.0",
                capabilities=(cap,),
            )
            self.assertEqual(len(desc.capabilities), 1)
            self.assertEqual(desc.capabilities[0], cap)

    def test_mapping_all_linux_capabilities(self):
        mappings = {
            LinuxCapability.SYSTEM_INFO: DeviceCapability.SYSTEM_INFO,
            LinuxCapability.STORAGE_INFO: DeviceCapability.STORAGE_QUERY,
            LinuxCapability.NETWORK_INFO: DeviceCapability.STATUS_QUERY,
            LinuxCapability.SERVICE_STATUS: DeviceCapability.STATUS_QUERY,
        }
        for linux_cap, device_cap in mappings.items():
            mapping = LinuxCapabilityMapping(
                linux_capability=linux_cap,
                device_capability=device_cap,
            )
            self.assertEqual(mapping.linux_capability, linux_cap)

    def test_descriptor_whitespace_id_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            LinuxAdapterDescriptor(adapter_id="   ", version="1.0.0", capabilities=())

    def test_descriptor_whitespace_version_rejected(self):
        with self.assertRaises(InvalidLinuxAdapterError):
            LinuxAdapterDescriptor(adapter_id="linux-001", version="   ", capabilities=())

    def test_provider_supports_false(self):
        class MockProvider(LinuxAdapterProvider):
            def descriptor(self):
                return LinuxAdapterDescriptor(
                    adapter_id="linux-001", version="1.0.0", capabilities=(),
                )
            def supports(self, capability):
                return False
            def execute(self, operation):
                pass
        provider = MockProvider()
        self.assertFalse(provider.supports(LinuxCapability.SYSTEM_INFO))

    def test_error_messages_safe(self):
        try:
            raise LinuxAdapterError("test")
        except LinuxAdapterError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_capability_error_message(self):
        exc = LinuxCapabilityError("cap error")
        self.assertIn("cap error", str(exc))

    def test_operation_error_message(self):
        exc = LinuxOperationError("op error")
        self.assertIn("op error", str(exc))

    def test_descriptor_no_command(self):
        desc = LinuxAdapterDescriptor(
            adapter_id="linux-001", version="1.0.0",
            capabilities=(LinuxCapability.SYSTEM_INFO,),
        )
        self.assertFalse(hasattr(desc, "command"))

    def test_descriptor_no_ssh(self):
        desc = LinuxAdapterDescriptor(
            adapter_id="linux-001", version="1.0.0",
            capabilities=(LinuxCapability.SYSTEM_INFO,),
        )
        self.assertFalse(hasattr(desc, "ssh"))

    def test_mapping_frozen_repr(self):
        mapping = LinuxCapabilityMapping(
            linux_capability=LinuxCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        r = repr(mapping)
        self.assertIn("SYSTEM_INFO", r)


if __name__ == "__main__":
    unittest.main()
