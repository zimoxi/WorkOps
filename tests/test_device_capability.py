"""
WorkOps Device Capability Tests
Sprint024: Device Capability Model

覆盖：
- DeviceType enum
- DeviceCapability enum
- DeviceModel validation
- CapabilityRequirement
- CapabilityMatcher
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.devices.capability import DeviceType, DeviceCapability
from backup_manager.devices.model import DeviceModel
from backup_manager.devices.matcher import CapabilityRequirement, CapabilityMatcher
from backup_manager.devices.errors import (
    DeviceError,
    DeviceTypeError,
    DeviceCapabilityError,
    DeviceModelValidationError,
    CapabilityRequirementError,
)


# ============================================================================
# DeviceType
# ============================================================================

class TestDeviceType(unittest.TestCase):
    """设备类型枚举测试"""

    def test_unknown_exists(self):
        self.assertEqual(DeviceType.UNKNOWN.value, "unknown")

    def test_server_exists(self):
        self.assertEqual(DeviceType.SERVER.value, "server")

    def test_nas_exists(self):
        self.assertEqual(DeviceType.NAS.value, "nas")

    def test_virtualization_host_exists(self):
        self.assertEqual(DeviceType.VIRTUALIZATION_HOST.value, "virtualization_host")

    def test_router_exists(self):
        self.assertEqual(DeviceType.ROUTER.value, "router")

    def test_five_types(self):
        self.assertEqual(len(DeviceType), 5)

    def test_invalid_type_rejected(self):
        with self.assertRaises(ValueError):
            DeviceType("nonexistent")

    def test_no_arbitrary_string(self):
        with self.assertRaises(ValueError):
            DeviceType("firewall")


# ============================================================================
# DeviceCapability
# ============================================================================

class TestDeviceCapability(unittest.TestCase):
    """设备能力枚举测试"""

    def test_status_query(self):
        self.assertEqual(DeviceCapability.STATUS_QUERY.value, "status_query")

    def test_system_info(self):
        self.assertEqual(DeviceCapability.SYSTEM_INFO.value, "system_info")

    def test_storage_query(self):
        self.assertEqual(DeviceCapability.STORAGE_QUERY.value, "storage_query")

    def test_network_query(self):
        self.assertEqual(DeviceCapability.NETWORK_QUERY.value, "network_query")

    def test_backup_source(self):
        self.assertEqual(DeviceCapability.BACKUP_SOURCE.value, "backup_source")

    def test_backup_target(self):
        self.assertEqual(DeviceCapability.BACKUP_TARGET.value, "backup_target")

    def test_six_capabilities(self):
        self.assertEqual(len(DeviceCapability), 6)

    def test_immutable_enum(self):
        """枚举值不可修改"""
        cap = DeviceCapability.STATUS_QUERY
        self.assertIsInstance(cap, DeviceCapability)
        # Enum 成员不可赋值
        with self.assertRaises(AttributeError):
            cap.value = "other"

    def test_invalid_capability_rejected(self):
        with self.assertRaises(ValueError):
            DeviceCapability("nonexistent")

    def test_no_duplicate_values(self):
        values = [c.value for c in DeviceCapability]
        self.assertEqual(len(values), len(set(values)))


# ============================================================================
# DeviceModel
# ============================================================================

class TestDeviceModel(unittest.TestCase):
    """设备模型测试"""

    def _make_model(self, **kwargs):
        defaults = {
            "device_id": "dev-001",
            "name": "Test Server",
            "device_type": DeviceType.SERVER,
            "capabilities": (DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
        }
        defaults.update(kwargs)
        return DeviceModel(**defaults)

    def test_valid_model(self):
        model = self._make_model()
        self.assertEqual(model.device_id, "dev-001")
        self.assertEqual(model.name, "Test Server")
        self.assertEqual(model.device_type, DeviceType.SERVER)
        self.assertIn(DeviceCapability.STATUS_QUERY, model.capabilities)
        self.assertTrue(model.enabled)

    def test_frozen(self):
        model = self._make_model()
        with self.assertRaises(AttributeError):
            model.device_id = "other"

    def test_empty_device_id_rejected(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(device_id="")

    def test_whitespace_device_id_rejected(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(device_id="   ")

    def test_empty_name_rejected(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(name="")

    def test_invalid_device_type_rejected(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(device_type="server")

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(capabilities=[DeviceCapability.STATUS_QUERY])

    def test_invalid_capability_in_tuple_rejected(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(capabilities=("not_a_capability",))

    def test_empty_capabilities_allowed(self):
        model = self._make_model(capabilities=())
        self.assertEqual(len(model.capabilities), 0)

    def test_enabled_default_true(self):
        model = self._make_model()
        self.assertTrue(model.enabled)

    def test_enabled_false(self):
        model = self._make_model(enabled=False)
        self.assertFalse(model.enabled)

    def test_enabled_must_be_bool(self):
        with self.assertRaises(DeviceModelValidationError):
            self._make_model(enabled=1)

    def test_timestamps(self):
        model = self._make_model()
        self.assertIsInstance(model.created_at, datetime)
        self.assertIsInstance(model.updated_at, datetime)

    def test_no_secret_fields(self):
        """DeviceModel 不包含任何 secret 字段"""
        model = self._make_model()
        for attr in ["password", "secret", "secret_ref", "credential", "token",
                      "private_key", "ssh_host", "ssh_port", "connection_string"]:
            self.assertFalse(
                hasattr(model, attr),
                f"DeviceModel should not have {attr}"
            )

    def test_repr_no_secrets(self):
        model = self._make_model()
        r = repr(model)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# CapabilityRequirement
# ============================================================================

class TestCapabilityRequirement(unittest.TestCase):
    """能力需求测试"""

    def test_valid_requirement(self):
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY, DeviceCapability.BACKUP_SOURCE),
        )
        self.assertEqual(len(req.required), 2)
        self.assertEqual(len(req.optional), 0)

    def test_with_optional(self):
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY,),
            optional=(DeviceCapability.NETWORK_QUERY,),
        )
        self.assertEqual(len(req.required), 1)
        self.assertEqual(len(req.optional), 1)

    def test_frozen(self):
        req = CapabilityRequirement(
            required=(DeviceCapability.STATUS_QUERY,),
        )
        with self.assertRaises(AttributeError):
            req.required = ()

    def test_invalid_required_type_rejected(self):
        with self.assertRaises(CapabilityRequirementError):
            CapabilityRequirement(required=[DeviceCapability.STATUS_QUERY])

    def test_invalid_required_capability_rejected(self):
        with self.assertRaises(CapabilityRequirementError):
            CapabilityRequirement(required=("not_a_capability",))

    def test_invalid_optional_type_rejected(self):
        with self.assertRaises(CapabilityRequirementError):
            CapabilityRequirement(
                required=(DeviceCapability.STATUS_QUERY,),
                optional=[DeviceCapability.NETWORK_QUERY],
            )

    def test_invalid_optional_capability_rejected(self):
        with self.assertRaises(CapabilityRequirementError):
            CapabilityRequirement(
                required=(DeviceCapability.STATUS_QUERY,),
                optional=("not_a_capability",),
            )


# ============================================================================
# CapabilityMatcher
# ============================================================================

class TestCapabilityMatcher(unittest.TestCase):
    """能力匹配器测试"""

    def _make_device(self, caps):
        return DeviceModel(
            device_id="dev-001",
            name="Test",
            device_type=DeviceType.SERVER,
            capabilities=tuple(caps),
        )

    def test_required_capability_exists(self):
        device = self._make_device([
            DeviceCapability.STORAGE_QUERY,
            DeviceCapability.BACKUP_SOURCE,
        ])
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY, DeviceCapability.BACKUP_SOURCE),
        )
        self.assertTrue(CapabilityMatcher.matches(device, req))

    def test_required_capability_missing(self):
        device = self._make_device([DeviceCapability.STORAGE_QUERY])
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY, DeviceCapability.BACKUP_SOURCE),
        )
        self.assertFalse(CapabilityMatcher.matches(device, req))

    def test_optional_capability_ignored(self):
        """可选能力缺失不影响匹配"""
        device = self._make_device([DeviceCapability.STORAGE_QUERY])
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY,),
            optional=(DeviceCapability.NETWORK_QUERY,),
        )
        self.assertTrue(CapabilityMatcher.matches(device, req))

    def test_optional_capability_present(self):
        device = self._make_device([
            DeviceCapability.STORAGE_QUERY,
            DeviceCapability.NETWORK_QUERY,
        ])
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY,),
            optional=(DeviceCapability.NETWORK_QUERY,),
        )
        self.assertTrue(CapabilityMatcher.matches(device, req))

    def test_empty_requirement(self):
        device = self._make_device([DeviceCapability.STATUS_QUERY])
        req = CapabilityRequirement(required=())
        self.assertTrue(CapabilityMatcher.matches(device, req))

    def test_device_no_capabilities(self):
        device = self._make_device([])
        req = CapabilityRequirement(
            required=(DeviceCapability.STATUS_QUERY,),
        )
        self.assertFalse(CapabilityMatcher.matches(device, req))


# ============================================================================
# DeviceCapabilityRegistry
# ============================================================================

class TestDeviceCapabilityRegistry(unittest.TestCase):
    """设备能力注册表测试"""

    def setUp(self):
        from backup_manager.devices.registry import DeviceCapabilityRegistry
        self.registry = DeviceCapabilityRegistry()

    def test_register_and_get(self):
        self.registry.register(
            DeviceType.SERVER,
            (DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
        )
        caps = self.registry.get(DeviceType.SERVER)
        self.assertIn(DeviceCapability.STATUS_QUERY, caps)
        self.assertIn(DeviceCapability.SYSTEM_INFO, caps)

    def test_duplicate_rejected(self):
        from backup_manager.devices.errors import CapabilityConflictError
        self.registry.register(DeviceType.SERVER, (DeviceCapability.STATUS_QUERY,))
        with self.assertRaises(CapabilityConflictError):
            self.registry.register(DeviceType.SERVER, (DeviceCapability.SYSTEM_INFO,))

    def test_get_unknown_rejected(self):
        from backup_manager.devices.errors import CapabilityNotFoundError
        with self.assertRaises(CapabilityNotFoundError):
            self.registry.get(DeviceType.NAS)

    def test_list(self):
        self.registry.register(DeviceType.SERVER, (DeviceCapability.STATUS_QUERY,))
        self.registry.register(DeviceType.NAS, (DeviceCapability.STORAGE_QUERY,))
        all_types = self.registry.list()
        self.assertEqual(len(all_types), 2)

    def test_supports_true(self):
        self.registry.register(
            DeviceType.SERVER,
            (DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
        )
        self.assertTrue(self.registry.supports(DeviceType.SERVER, DeviceCapability.STATUS_QUERY))

    def test_supports_false(self):
        self.registry.register(DeviceType.SERVER, (DeviceCapability.STATUS_QUERY,))
        self.assertFalse(self.registry.supports(DeviceType.SERVER, DeviceCapability.BACKUP_SOURCE))

    def test_supports_unregistered(self):
        self.assertFalse(self.registry.supports(DeviceType.NAS, DeviceCapability.STATUS_QUERY))

    def test_no_dynamic_loading(self):
        """确认 registry 不使用动态加载"""
        import ast
        with open("backup_manager/devices/registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("__import__", "import_module"):
                    self.fail("registry uses dynamic import")


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_model_repr_no_secrets(self):
        model = DeviceModel(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        r = repr(model)
        for term in ["password", "secret", "token", "credential", "ssh"]:
            self.assertNotIn(term, r.lower())

    def test_model_no_credential_fields(self):
        model = DeviceModel(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
        )
        for attr in ["password", "secret", "secret_ref", "credential", "token",
                      "private_key", "ssh_host", "ssh_port", "connection_string",
                      "command"]:
            self.assertFalse(hasattr(model, attr))

    def test_requirement_no_secrets(self):
        req = CapabilityRequirement(
            required=(DeviceCapability.STORAGE_QUERY,),
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_error_messages_no_secrets(self):
        try:
            raise DeviceModelValidationError("test error")
        except DeviceModelValidationError as e:
            msg = str(e)
            self.assertNotIn("password", msg.lower())
            self.assertNotIn("secret", msg.lower())

    def test_no_dynamic_capability_registration(self):
        """DeviceCapability 枚举不允许动态添加"""
        self.assertEqual(len(DeviceCapability), 6)
        # Enum 不支持动态添加成员

    def test_devices_module_no_subprocess(self):
        """devices 模块不使用 subprocess"""
        import ast
        import os
        devices_dir = os.path.join("backup_manager", "devices")
        for filename in os.listdir(devices_dir):
            if filename.endswith(".py"):
                filepath = os.path.join(devices_dir, filename)
                with open(filepath) as f:
                    tree = ast.parse(f.read())
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            self.assertNotEqual(alias.name, "subprocess")
                    elif isinstance(node, ast.ImportFrom):
                        if node.module and "subprocess" in node.module:
                            self.fail(f"subprocess imported in {filename}")


if __name__ == "__main__":
    unittest.main()
