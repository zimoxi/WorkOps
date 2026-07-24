"""
WorkOps OMV Adapter v1 Tests
Sprint050: OMV Adapter v1 Foundation

覆盖：
- OMVCapability enum
- OMVOperation enum
- OMVAdapterDescriptor validation
- OMVAdapterProvider contract
- OMVCapabilityMapping validation
- Error model
- Security boundary
"""

import unittest

from backup_manager.adapters.omv.v1_capability import OMVCapability, OMVOperation
from backup_manager.adapters.omv.v1_model import OMVAdapterDescriptor
from backup_manager.adapters.omv.v1_provider import OMVAdapterProvider
from backup_manager.adapters.omv.v1_capability_mapping import OMVCapabilityMapping
from backup_manager.adapters.omv.v1_errors import (
    OMVAdapterV1Error,
    InvalidOMVAdapterError,
    OMVCapabilityError,
    OMVOperationError,
)
from backup_manager.devices.capability import DeviceCapability


# ============================================================================
# OMVCapability
# ============================================================================

class TestOMVCapability(unittest.TestCase):
    """OMV 能力测试"""

    def test_system_info(self):
        self.assertEqual(OMVCapability.SYSTEM_INFO.value, "system_info")

    def test_storage_info(self):
        self.assertEqual(OMVCapability.STORAGE_INFO.value, "storage_info")

    def test_share_info(self):
        self.assertEqual(OMVCapability.SHARE_INFO.value, "share_info")

    def test_backup_capability(self):
        self.assertEqual(OMVCapability.BACKUP_CAPABILITY.value, "backup_capability")

    def test_four_capabilities(self):
        self.assertEqual(len(OMVCapability), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            OMVCapability("nonexistent")


# ============================================================================
# OMVOperation
# ============================================================================

class TestOMVOperation(unittest.TestCase):
    """OMV 操作测试"""

    def test_query_system(self):
        self.assertEqual(OMVOperation.QUERY_SYSTEM.value, "query_system")

    def test_query_storage(self):
        self.assertEqual(OMVOperation.QUERY_STORAGE.value, "query_storage")

    def test_query_share(self):
        self.assertEqual(OMVOperation.QUERY_SHARE.value, "query_share")

    def test_query_backup(self):
        self.assertEqual(OMVOperation.QUERY_BACKUP.value, "query_backup")

    def test_four_operations(self):
        self.assertEqual(len(OMVOperation), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            OMVOperation("nonexistent")


# ============================================================================
# OMVAdapterDescriptor
# ============================================================================

class TestOMVAdapterDescriptor(unittest.TestCase):
    """OMV 适配器描述符测试"""

    def _make_descriptor(self, **kwargs):
        defaults = {
            "adapter_id": "omv-001",
            "version": "1.0.0",
            "capabilities": (OMVCapability.SYSTEM_INFO, OMVCapability.STORAGE_INFO),
        }
        defaults.update(kwargs)
        return OMVAdapterDescriptor(**defaults)

    def test_valid_descriptor(self):
        desc = self._make_descriptor()
        self.assertEqual(desc.adapter_id, "omv-001")
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
        with self.assertRaises(InvalidOMVAdapterError):
            self._make_descriptor(adapter_id="")

    def test_empty_version_rejected(self):
        with self.assertRaises(InvalidOMVAdapterError):
            self._make_descriptor(version="")

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(InvalidOMVAdapterError):
            self._make_descriptor(capabilities=[OMVCapability.SYSTEM_INFO])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(InvalidOMVAdapterError):
            self._make_descriptor(capabilities=("bad",))

    def test_empty_capabilities_allowed(self):
        desc = self._make_descriptor(capabilities=())
        self.assertEqual(len(desc.capabilities), 0)

    def test_multiple_capabilities(self):
        desc = self._make_descriptor(capabilities=(
            OMVCapability.SYSTEM_INFO,
            OMVCapability.STORAGE_INFO,
            OMVCapability.SHARE_INFO,
            OMVCapability.BACKUP_CAPABILITY,
        ))
        self.assertEqual(len(desc.capabilities), 4)

    def test_no_forbidden_fields(self):
        desc = self._make_descriptor()
        for attr in ["password", "credential", "secret", "token", "ssh", "command",
                      "ip", "hostname", "api_key", "connection_string"]:
            self.assertFalse(hasattr(desc, attr))


# ============================================================================
# OMVAdapterProvider Contract
# ============================================================================

class TestOMVAdapterProviderContract(unittest.TestCase):
    """OMV 适配器提供者契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVAdapterProvider, ABC))

    def test_has_descriptor(self):
        self.assertTrue(hasattr(OMVAdapterProvider, "descriptor"))

    def test_has_supports(self):
        self.assertTrue(hasattr(OMVAdapterProvider, "supports"))

    def test_has_execute(self):
        self.assertTrue(hasattr(OMVAdapterProvider, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OMVAdapterProvider()

    def test_concrete_subclass(self):
        class MockProvider(OMVAdapterProvider):
            def descriptor(self):
                return OMVAdapterDescriptor(
                    adapter_id="omv-001", version="1.0.0",
                    capabilities=(OMVCapability.SYSTEM_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        self.assertEqual(provider.descriptor().adapter_id, "omv-001")
        self.assertTrue(provider.supports(OMVCapability.SYSTEM_INFO))
        self.assertFalse(provider.supports(OMVCapability.STORAGE_INFO))
        result = provider.execute(OMVOperation.QUERY_SYSTEM)
        self.assertEqual(result["status"], "ok")

    def test_missing_descriptor(self):
        class BadProvider(OMVAdapterProvider):
            def supports(self, capability):
                return False
            def execute(self, operation):
                pass
        with self.assertRaises(TypeError):
            BadProvider()


# ============================================================================
# OMVCapabilityMapping
# ============================================================================

class TestOMVCapabilityMapping(unittest.TestCase):
    """OMV 能力映射测试"""

    def test_valid_mapping(self):
        mapping = OMVCapabilityMapping(
            omv_capability=OMVCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        self.assertEqual(mapping.omv_capability, OMVCapability.SYSTEM_INFO)
        self.assertEqual(mapping.device_capability, DeviceCapability.SYSTEM_INFO)

    def test_frozen(self):
        mapping = OMVCapabilityMapping(
            omv_capability=OMVCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        with self.assertRaises(AttributeError):
            mapping.omv_capability = OMVCapability.STORAGE_INFO

    def test_slots(self):
        mapping = OMVCapabilityMapping(
            omv_capability=OMVCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        with self.assertRaises(AttributeError):
            mapping.__dict__

    def test_invalid_omv_capability_rejected(self):
        with self.assertRaises(InvalidOMVAdapterError):
            OMVCapabilityMapping(
                omv_capability="system_info",
                device_capability=DeviceCapability.SYSTEM_INFO,
            )

    def test_invalid_device_capability_rejected(self):
        with self.assertRaises(InvalidOMVAdapterError):
            OMVCapabilityMapping(
                omv_capability=OMVCapability.SYSTEM_INFO,
                device_capability="system_info",
            )

    def test_storage_mapping(self):
        mapping = OMVCapabilityMapping(
            omv_capability=OMVCapability.STORAGE_INFO,
            device_capability=DeviceCapability.STORAGE_QUERY,
        )
        self.assertEqual(mapping.omv_capability, OMVCapability.STORAGE_INFO)


# ============================================================================
# Error Model
# ============================================================================

class TestOMVAdapterV1Errors(unittest.TestCase):
    """错误模型测试"""

    def test_adapter_error(self):
        with self.assertRaises(OMVAdapterV1Error):
            raise OMVAdapterV1Error("test")

    def test_invalid_adapter_error(self):
        with self.assertRaises(OMVAdapterV1Error):
            raise InvalidOMVAdapterError("test")

    def test_capability_error(self):
        with self.assertRaises(OMVAdapterV1Error):
            raise OMVCapabilityError("test")

    def test_operation_error(self):
        with self.assertRaises(OMVAdapterV1Error):
            raise OMVOperationError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (OMVAdapterV1Error, ("test",)),
            (InvalidOMVAdapterError, ("test",)),
            (OMVCapabilityError, ("test",)),
            (OMVOperationError, ("test",)),
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
        desc = OMVAdapterDescriptor(
            adapter_id="omv-001", version="1.0.0",
            capabilities=(OMVCapability.SYSTEM_INFO,),
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(desc, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["v1_capability.py", "v1_model.py", "v1_provider.py",
                         "v1_capability_mapping.py", "v1_errors.py"]:
            filepath = os.path.join("backup_manager", "adapters", "omv", filename)
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
            filepath = os.path.join("backup_manager", "adapters", "omv", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_provider_lifecycle(self):
        """完整提供者生命周期"""
        class MockProvider(OMVAdapterProvider):
            def descriptor(self):
                return OMVAdapterDescriptor(
                    adapter_id="omv-001", version="1.0.0",
                    capabilities=(OMVCapability.SYSTEM_INFO,),
                )
            def supports(self, capability):
                return capability in self.descriptor().capabilities
            def execute(self, operation):
                return {"status": "ok"}
        provider = MockProvider()
        desc = provider.descriptor()
        self.assertEqual(desc.adapter_id, "omv-001")
        self.assertTrue(provider.supports(OMVCapability.SYSTEM_INFO))
        result = provider.execute(OMVOperation.QUERY_SYSTEM)
        self.assertEqual(result["status"], "ok")


# ============================================================================
# Extended Tests
# ============================================================================

class TestOMVAdapterV1Extended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidOMVAdapterError, OMVAdapterV1Error))
        self.assertTrue(issubclass(OMVCapabilityError, OMVAdapterV1Error))
        self.assertTrue(issubclass(OMVOperationError, OMVAdapterV1Error))

    def test_descriptor_repr_no_secrets(self):
        desc = OMVAdapterDescriptor(
            adapter_id="omv-001", version="1.0.0",
            capabilities=(OMVCapability.SYSTEM_INFO,),
        )
        r = repr(desc)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_mapping_repr_no_secrets(self):
        mapping = OMVCapabilityMapping(
            omv_capability=OMVCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        r = repr(mapping)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_all_capabilities(self):
        for cap in OMVCapability:
            desc = OMVAdapterDescriptor(
                adapter_id="omv-001", version="1.0.0",
                capabilities=(cap,),
            )
            self.assertIn(cap, desc.capabilities)

    def test_all_operations(self):
        for op in OMVOperation:
            self.assertIsInstance(op.value, str)

    def test_provider_supports_false(self):
        class MockProvider(OMVAdapterProvider):
            def descriptor(self):
                return OMVAdapterDescriptor(
                    adapter_id="omv-001", version="1.0.0", capabilities=(),
                )
            def supports(self, capability):
                return False
            def execute(self, operation):
                pass
        provider = MockProvider()
        self.assertFalse(provider.supports(OMVCapability.SYSTEM_INFO))

    def test_error_messages_safe(self):
        try:
            raise OMVAdapterV1Error("test")
        except OMVAdapterV1Error as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_descriptor_no_api_key(self):
        desc = OMVAdapterDescriptor(
            adapter_id="omv-001", version="1.0.0",
            capabilities=(OMVCapability.SYSTEM_INFO,),
        )
        self.assertFalse(hasattr(desc, "api_key"))

    def test_descriptor_no_connection_string(self):
        desc = OMVAdapterDescriptor(
            adapter_id="omv-001", version="1.0.0",
            capabilities=(OMVCapability.SYSTEM_INFO,),
        )
        self.assertFalse(hasattr(desc, "connection_string"))

    def test_mapping_all_omv_capabilities(self):
        mappings = {
            OMVCapability.SYSTEM_INFO: DeviceCapability.SYSTEM_INFO,
            OMVCapability.STORAGE_INFO: DeviceCapability.STORAGE_QUERY,
            OMVCapability.SHARE_INFO: DeviceCapability.STATUS_QUERY,
            OMVCapability.BACKUP_CAPABILITY: DeviceCapability.STATUS_QUERY,
        }
        for omv_cap, device_cap in mappings.items():
            mapping = OMVCapabilityMapping(
                omv_capability=omv_cap,
                device_capability=device_cap,
            )
            self.assertEqual(mapping.omv_capability, omv_cap)

    def test_descriptor_whitespace_id_rejected(self):
        with self.assertRaises(InvalidOMVAdapterError):
            OMVAdapterDescriptor(adapter_id="   ", version="1.0.0", capabilities=())

    def test_descriptor_whitespace_version_rejected(self):
        with self.assertRaises(InvalidOMVAdapterError):
            OMVAdapterDescriptor(adapter_id="omv-001", version="   ", capabilities=())

    def test_descriptor_all_capabilities(self):
        for cap in OMVCapability:
            desc = OMVAdapterDescriptor(
                adapter_id="omv-001", version="1.0.0",
                capabilities=(cap,),
            )
            self.assertEqual(len(desc.capabilities), 1)
            self.assertEqual(desc.capabilities[0], cap)

    def test_capability_error_message(self):
        exc = OMVCapabilityError("cap error")
        self.assertIn("cap error", str(exc))

    def test_operation_error_message(self):
        exc = OMVOperationError("op error")
        self.assertIn("op error", str(exc))

    def test_mapping_frozen_repr(self):
        mapping = OMVCapabilityMapping(
            omv_capability=OMVCapability.SYSTEM_INFO,
            device_capability=DeviceCapability.SYSTEM_INFO,
        )
        r = repr(mapping)
        self.assertIn("SYSTEM_INFO", r)


if __name__ == "__main__":
    unittest.main()
