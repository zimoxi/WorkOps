"""
WorkOps PVE Adapter v1 Tests
Sprint049: PVE Adapter v1 Foundation

覆盖：
- PVECapability enum
- PVEOperation enum
- PVEAdapterDescriptor validation
- PVEAdapterProvider contract
- PVECapabilityMapping validation
- Error model
- Security boundary
"""

import unittest

from backup_manager.adapters.pve.v1_capability import PVECapability, PVEOperation
from backup_manager.adapters.pve.v1_model import PVEAdapterDescriptor
from backup_manager.adapters.pve.v1_provider import PVEAdapterProvider
from backup_manager.adapters.pve.v1_capability_mapping import PVECapabilityMapping
from backup_manager.adapters.pve.v1_errors import (
    PVEAdapterV1Error,
    InvalidPVEAdapterError,
    PVECapabilityError,
    PVEOperationError,
)
from backup_manager.devices.capability import DeviceCapability


# ============================================================================
# PVECapability
# ============================================================================

class TestPVECapability(unittest.TestCase):
    """PVE 能力测试"""

    def test_node_info(self):
        self.assertEqual(PVECapability.NODE_INFO.value, "node_info")

    def test_vm_info(self):
        self.assertEqual(PVECapability.VM_INFO.value, "vm_info")

    def test_storage_info(self):
        self.assertEqual(PVECapability.STORAGE_INFO.value, "storage_info")

    def test_backup_capability(self):
        self.assertEqual(PVECapability.BACKUP_CAPABILITY.value, "backup_capability")

    def test_four_capabilities(self):
        self.assertEqual(len(PVECapability), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PVECapability("nonexistent")


# ============================================================================
# PVEOperation
# ============================================================================

class TestPVEOperation(unittest.TestCase):
    """PVE 操作测试"""

    def test_query_node(self):
        self.assertEqual(PVEOperation.QUERY_NODE.value, "query_node")

    def test_query_vm(self):
        self.assertEqual(PVEOperation.QUERY_VM.value, "query_vm")

    def test_query_storage(self):
        self.assertEqual(PVEOperation.QUERY_STORAGE.value, "query_storage")

    def test_query_backup(self):
        self.assertEqual(PVEOperation.QUERY_BACKUP.value, "query_backup")

    def test_four_operations(self):
        self.assertEqual(len(PVEOperation), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            PVEOperation("nonexistent")


# ============================================================================
# PVEAdapterDescriptor
# ============================================================================

class TestPVEAdapterDescriptor(unittest.TestCase):
    """PVE 适配器描述符测试"""

    def _make_descriptor(self, **kwargs):
        defaults = {
            "adapter_id": "pve-001",
            "version": "1.0.0",
            "capabilities": (PVECapability.NODE_INFO, PVECapability.VM_INFO),
        }
        defaults.update(kwargs)
        return PVEAdapterDescriptor(**defaults)

    def test_valid_descriptor(self):
        desc = self._make_descriptor()
        self.assertEqual(desc.adapter_id, "pve-001")
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
        with self.assertRaises(InvalidPVEAdapterError):
            self._make_descriptor(adapter_id="")

    def test_empty_version_rejected(self):
        with self.assertRaises(InvalidPVEAdapterError):
            self._make_descriptor(version="")

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(InvalidPVEAdapterError):
            self._make_descriptor(capabilities=[PVECapability.NODE_INFO])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(InvalidPVEAdapterError):
            self._make_descriptor(capabilities=("bad",))

    def test_empty_capabilities_allowed(self):
        desc = self._make_descriptor(capabilities=())
        self.assertEqual(len(desc.capabilities), 0)

    def test_multiple_capabilities(self):
        desc = self._make_descriptor(capabilities=(
            PVECapability.NODE_INFO,
            PVECapability.VM_INFO,
            PVECapability.STORAGE_INFO,
            PVECapability.BACKUP_CAPABILITY,
        ))
        self.assertEqual(len(desc.capabilities), 4)

    def test_no_forbidden_fields(self):
        desc = self._make_descriptor()
        for attr in ["password", "credential", "secret", "token", "ssh", "command",
                      "ip", "hostname", "cluster_connection"]:
            self.assertFalse(hasattr(desc, attr))


# ============================================================================
# PVEAdapterProvider Contract
# ============================================================================

class TestPVEAdapterProviderContract(unittest.TestCase):
    """PVE 适配器提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEAdapterProvider, ABC))

    def test_has_descriptor(self):
        self.assertTrue(hasattr(PVEAdapterProvider, "descriptor"))

    def test_has_supports(self):
        self.assertTrue(hasattr(PVEAdapterProvider, "supports"))

    def test_has_execute(self):
        self.assertTrue(hasattr(PVEAdapterProvider, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PVEAdapterProvider()

    def test_concrete_subclass(self):
        class MockProvider(PVEAdapterProvider):
            def descriptor(self):
                return PVEAdapterDescriptor(
                    adapter_id="pve-001", version="1.0.0",
                    capabilities=(PVECapability.NODE_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        self.assertEqual(provider.descriptor().adapter_id, "pve-001")
        self.assertTrue(provider.supports(PVECapability.NODE_INFO))
        self.assertFalse(provider.supports(PVECapability.VM_INFO))
        result = provider.execute(PVEOperation.QUERY_NODE)
        self.assertEqual(result["status"], "ok")

    def test_missing_descriptor(self):
        class BadProvider(PVEAdapterProvider):
            def supports(self, capability):
                return False
            def execute(self, operation):
                pass
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# PVECapabilityMapping
# ============================================================================

class TestPVECapabilityMapping(unittest.TestCase):
    """PVE 能力映射测试"""

    def test_valid_mapping(self):
        mapping = PVECapabilityMapping(
            pve_capability=PVECapability.NODE_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        self.assertEqual(mapping.pve_capability, PVECapability.NODE_INFO)
        self.assertEqual(mapping.device_capability, DeviceCapability.SYSTEM_INFO)

    def test_frozen(self):
        mapping = PVECapabilityMapping(
            pve_capability=PVECapability.NODE_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        with self.assertRaises(AttributeError):
            mapping.pve_capability = PVECapability.VM_INFO

    def test_slots(self):
        mapping = PVECapabilityMapping(
            pve_capability=PVECapability.NODE_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        with self.assertRaises(AttributeError):
            mapping.__dict__

    def test_invalid_pve_capability_rejected(self):
        with self.assertRaises(InvalidPVEAdapterError):
            PVECapabilityMapping(
                pve_capability="node_info",
                device_capability=DeviceCapability.SYSTEM_INFO,
            )

    def test_invalid_device_capability_rejected(self):
        with self.assertRaises(InvalidPVEAdapterError):
            PVECapabilityMapping(
                pve_capability=PVECapability.NODE_INFO,
                device_capability="system_info",
            )

    def test_storage_mapping(self):
        mapping = PVECapabilityMapping(
            pve_capability=PVECapability.STORAGE_INFO,
            device_capability=DeviceCapability.STORAGE_QUERY,
        )
        self.assertEqual(mapping.pve_capability, PVECapability.STORAGE_INFO)


# ============================================================================
# Error Model
# ============================================================================

class TestPVEAdapterV1Errors(unittest.TestCase):
    """错误模型测试"""

    def test_adapter_error(self):
        with self.assertRaises(PVEAdapterV1Error):
            raise PVEAdapterV1Error("test")

    def test_invalid_adapter_error(self):
        with self.assertRaises(PVEAdapterV1Error):
            raise InvalidPVEAdapterError("test")

    def test_capability_error(self):
        with self.assertRaises(PVEAdapterV1Error):
            raise PVECapabilityError("test")

    def test_operation_error(self):
        with self.assertRaises(PVEAdapterV1Error):
            raise PVEOperationError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (PVEAdapterV1Error, ("test",)),
            (InvalidPVEAdapterError, ("test",)),
            (PVECapabilityError, ("test",)),
            (PVEOperationError, ("test",)),
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
        desc = PVEAdapterDescriptor(
            adapter_id="pve-001", version="1.0.0",
            capabilities=(PVECapability.NODE_INFO,),
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(desc, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["v1_capability.py", "v1_model.py", "v1_provider.py",
                         "v1_capability_mapping.py", "v1_errors.py"]:
            filepath = os.path.join("backup_manager", "adapters", "pve", filename)
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
        for filename in ["v1_capability.py", "v1_model.py", "v1_provider.py",
                         "v1_capability_mapping.py", "v1_errors.py"]:
            filepath = os.path.join("backup_manager", "adapters", "pve", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_provider_lifecycle(self):
        """完整提供者生命周期"""
        class MockProvider(PVEAdapterProvider):
            def descriptor(self):
                return PVEAdapterDescriptor(
                    adapter_id="pve-001", version="1.0.0",
                    capabilities=(PVECapability.NODE_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        desc = provider.descriptor()
        self.assertEqual(desc.adapter_id, "pve-001")
        self.assertTrue(provider.supports(PVECapability.NODE_INFO))
        result = provider.execute(PVEOperation.QUERY_NODE)
        self.assertEqual(result["status"], "ok")


# ============================================================================
# Extended Tests
# ============================================================================

class TestPVEAdapterV1Extended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidPVEAdapterError, PVEAdapterV1Error))
        self.assertTrue(issubclass(PVECapabilityError, PVEAdapterV1Error))
        self.assertTrue(issubclass(PVEOperationError, PVEAdapterV1Error))

    def test_descriptor_repr_no_secrets(self):
        desc = PVEAdapterDescriptor(
            adapter_id="pve-001", version="1.0.0",
            capabilities=(PVECapability.NODE_INFO,),
        )
        r = repr(desc)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_mapping_repr_no_secrets(self):
        mapping = PVECapabilityMapping(
            pve_capability=PVECapability.NODE_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        r = repr(mapping)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_all_capabilities(self):
        for cap in PVECapability:
            desc = PVEAdapterDescriptor(
                adapter_id="pve-001", version="1.0.0",
                capabilities=(cap,),
            )
            self.assertIn(cap, desc.capabilities)

    def test_all_operations(self):
        for op in PVEOperation:
            self.assertIsInstance(op.value, str)

    def test_provider_supports_false(self):
        class MockProvider(PVEAdapterProvider):
            def descriptor(self):
                return PVEAdapterDescriptor(
                    adapter_id="pve-001", version="1.0.0", capabilities=(),
                )
            def supports(self, capability):
                return False
            def execute(self, operation):
                pass
        provider = MockProvider()
        self.assertFalse(provider.supports(PVECapability.NODE_INFO))

    def test_error_messages_safe(self):
        try:
            raise PVEAdapterV1Error("test")
        except PVEAdapterV1Error as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_descriptor_whitespace_id_rejected(self):
        with self.assertRaises(InvalidPVEAdapterError):
            PVEAdapterDescriptor(adapter_id="   ", version="1.0.0", capabilities=())

    def test_descriptor_whitespace_version_rejected(self):
        with self.assertRaises(InvalidPVEAdapterError):
            PVEAdapterDescriptor(adapter_id="pve-001", version="   ", capabilities=())

    def test_mapping_all_pve_capabilities(self):
        mappings = {
            PVECapability.NODE_INFO: DeviceCapability.SYSTEM_INFO,
            PVECapability.VM_INFO: DeviceCapability.SYSTEM_INFO,
            PVECapability.STORAGE_INFO: DeviceCapability.STORAGE_QUERY,
            PVECapability.BACKUP_CAPABILITY: DeviceCapability.STATUS_QUERY,
        }
        for pve_cap, device_cap in mappings.items():
            mapping = PVECapabilityMapping(
                pve_capability=pve_cap,
                device_capability=device_cap,
            )
            self.assertEqual(mapping.pve_capability, pve_cap)

    def test_descriptor_all_capabilities(self):
        for cap in PVECapability:
            desc = PVEAdapterDescriptor(
                adapter_id="pve-001", version="1.0.0",
                capabilities=(cap,),
            )
            self.assertEqual(len(desc.capabilities), 1)
            self.assertEqual(desc.capabilities[0], cap)

    def test_capability_error_message(self):
        exc = PVECapabilityError("cap error")
        self.assertIn("cap error", str(exc))

    def test_operation_error_message(self):
        exc = PVEOperationError("op error")
        self.assertIn("op error", str(exc))

    def test_descriptor_no_cluster_connection(self):
        desc = PVEAdapterDescriptor(
            adapter_id="pve-001", version="1.0.0",
            capabilities=(PVECapability.NODE_INFO,),
        )
        self.assertFalse(hasattr(desc, "cluster_connection"))

    def test_mapping_frozen_repr(self):
        mapping = PVECapabilityMapping(
            pve_capability=PVECapability.NODE_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        r = repr(mapping)
        self.assertIn("NODE_INFO", r)

    def test_provider_returns_descriptor(self):
        class MockProvider(PVEAdapterProvider):
            def descriptor(self):
                return PVEAdapterDescriptor(
                    adapter_id="pve-001", version="1.0.0",
                    capabilities=(PVECapability.NODE_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        desc = provider.descriptor()
        self.assertIsInstance(desc, PVEAdapterDescriptor)


if __name__ == "__main__":
    unittest.main()
