"""
WorkOps Device Inventory Tests
Sprint025: Device Inventory

覆盖：
- DeviceStatus enum
- DeviceRecord validation
- DeviceInventoryRepository
- DeviceInventoryService
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.devices.capability import DeviceType, DeviceCapability
from backup_manager.devices.status import DeviceStatus
from backup_manager.devices.inventory import DeviceRecord
from backup_manager.devices.repository import DeviceInventoryRepository
from backup_manager.devices.service import DeviceInventoryService
from backup_manager.devices.errors import (
    DeviceInventoryError,
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
)


# ============================================================================
# DeviceStatus
# ============================================================================

class TestDeviceStatus(unittest.TestCase):
    """设备状态枚举测试"""

    def test_unknown(self):
        self.assertEqual(DeviceStatus.UNKNOWN.value, "unknown")

    def test_active(self):
        self.assertEqual(DeviceStatus.ACTIVE.value, "active")

    def test_disabled(self):
        self.assertEqual(DeviceStatus.DISABLED.value, "disabled")

    def test_retired(self):
        self.assertEqual(DeviceStatus.RETIRED.value, "retired")

    def test_four_statuses(self):
        self.assertEqual(len(DeviceStatus), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            DeviceStatus("nonexistent")


# ============================================================================
# DeviceRecord
# ============================================================================

class TestDeviceRecord(unittest.TestCase):
    """设备记录测试"""

    def _make_record(self, **kwargs):
        defaults = {
            "device_id": "dev-001",
            "name": "Test Server",
            "device_type": DeviceType.SERVER,
            "capabilities": (DeviceCapability.STATUS_QUERY,),
            "adapter_type": "ssh_readonly",
        }
        defaults.update(kwargs)
        return DeviceRecord(**defaults)

    def test_valid_record(self):
        record = self._make_record()
        self.assertEqual(record.device_id, "dev-001")
        self.assertEqual(record.name, "Test Server")
        self.assertEqual(record.adapter_type, "ssh_readonly")
        self.assertEqual(record.status, DeviceStatus.UNKNOWN)

    def test_frozen(self):
        record = self._make_record()
        with self.assertRaises(AttributeError):
            record.device_id = "other"

    def test_slots(self):
        record = self._make_record()
        with self.assertRaises(AttributeError):
            record.__dict__

    def test_empty_device_id_rejected(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(device_id="")

    def test_empty_name_rejected(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(name="")

    def test_empty_adapter_type_rejected(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(adapter_type="")

    def test_invalid_device_type_rejected(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(device_type="server")

    def test_capabilities_must_be_tuple(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(capabilities=[DeviceCapability.STATUS_QUERY])

    def test_invalid_capability_rejected(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(capabilities=("bad",))

    def test_invalid_status_rejected(self):
        with self.assertRaises(DeviceInventoryError):
            self._make_record(status="active")

    def test_timezone_aware(self):
        record = self._make_record()
        self.assertIsNotNone(record.created_at.tzinfo)
        self.assertIsNotNone(record.updated_at.tzinfo)

    def test_custom_status(self):
        record = self._make_record(status=DeviceStatus.ACTIVE)
        self.assertEqual(record.status, DeviceStatus.ACTIVE)

    def test_no_forbidden_fields(self):
        record = self._make_record()
        for field in ["ip", "hostname", "port", "username", "password",
                       "credential", "secret", "token", "command", "ssh"]:
            self.assertFalse(hasattr(record, field))


# ============================================================================
# DeviceInventoryRepository
# ============================================================================

class TestDeviceInventoryRepository(unittest.TestCase):
    """设备清单仓库测试"""

    def setUp(self):
        self.repo = DeviceInventoryRepository()
        self.record = DeviceRecord(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )

    def test_add_and_get(self):
        self.repo.add(self.record)
        got = self.repo.get("dev-001")
        self.assertEqual(got.device_id, "dev-001")

    def test_duplicate_rejected(self):
        self.repo.add(self.record)
        with self.assertRaises(DeviceAlreadyExistsError):
            self.repo.add(self.record)

    def test_get_not_found(self):
        with self.assertRaises(DeviceNotFoundError):
            self.repo.get("nonexistent")

    def test_list(self):
        self.repo.add(self.record)
        record2 = DeviceRecord(
            device_id="dev-002",
            name="NAS",
            device_type=DeviceType.NAS,
            capabilities=(DeviceCapability.STORAGE_QUERY,),
            adapter_type="ssh_readonly",
        )
        self.repo.add(record2)
        devices = self.repo.list()
        self.assertEqual(len(devices), 2)

    def test_remove(self):
        self.repo.add(self.record)
        self.repo.remove("dev-001")
        self.assertEqual(self.repo.count(), 0)

    def test_remove_not_found(self):
        with self.assertRaises(DeviceNotFoundError):
            self.repo.remove("nonexistent")

    def test_count(self):
        self.assertEqual(self.repo.count(), 0)
        self.repo.add(self.record)
        self.assertEqual(self.repo.count(), 1)

    def test_add_non_record_rejected(self):
        with self.assertRaises(TypeError):
            self.repo.add("not_a_record")


# ============================================================================
# DeviceInventoryService
# ============================================================================

class TestDeviceInventoryService(unittest.TestCase):
    """设备清单服务测试"""

    def setUp(self):
        self.service = DeviceInventoryService()

    def test_register(self):
        record = self.service.register(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY, DeviceCapability.SYSTEM_INFO),
            adapter_type="ssh_readonly",
        )
        self.assertEqual(record.device_id, "dev-001")
        self.assertEqual(record.status, DeviceStatus.ACTIVE)

    def test_lookup(self):
        self.service.register(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )
        found = self.service.lookup("dev-001")
        self.assertEqual(found.name, "Test Server")

    def test_disable(self):
        self.service.register(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )
        disabled = self.service.disable("dev-001")
        self.assertEqual(disabled.status, DeviceStatus.DISABLED)

    def test_retire(self):
        self.service.register(
            device_id="dev-001",
            name="Test Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )
        retired = self.service.retire("dev-001")
        self.assertEqual(retired.status, DeviceStatus.RETIRED)

    def test_list_all(self):
        self.service.register(
            device_id="dev-001",
            name="Server",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )
        self.service.register(
            device_id="dev-002",
            name="NAS",
            device_type=DeviceType.NAS,
            capabilities=(DeviceCapability.STORAGE_QUERY,),
            adapter_type="ssh_readonly",
        )
        devices = self.service.list_all()
        self.assertEqual(len(devices), 2)

    def test_disable_not_found(self):
        with self.assertRaises(DeviceNotFoundError):
            self.service.disable("nonexistent")

    def test_retire_not_found(self):
        with self.assertRaises(DeviceNotFoundError):
            self.service.retire("nonexistent")

    def test_lookup_not_found(self):
        with self.assertRaises(DeviceNotFoundError):
            self.service.lookup("nonexistent")

    def test_no_connect_method(self):
        self.assertFalse(hasattr(self.service, "connect"))

    def test_no_execute_method(self):
        self.assertFalse(hasattr(self.service, "execute"))

    def test_no_scan_method(self):
        self.assertFalse(hasattr(self.service, "scan"))

    def test_no_discover_method(self):
        self.assertFalse(hasattr(self.service, "discover"))

    def test_repository_access(self):
        self.assertIsInstance(self.service.repository, DeviceInventoryRepository)


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_record_no_secrets(self):
        record = DeviceRecord(
            device_id="dev-001",
            name="Test",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )
        for attr in ["password", "secret", "secret_ref", "credential", "token",
                      "private_key", "ssh_host", "ssh_port", "connection_string",
                      "command", "ip", "hostname"]:
            self.assertFalse(hasattr(record, attr))

    def test_record_repr_no_secrets(self):
        record = DeviceRecord(
            device_id="dev-001",
            name="Test",
            device_type=DeviceType.SERVER,
            capabilities=(DeviceCapability.STATUS_QUERY,),
            adapter_type="ssh_readonly",
        )
        r = repr(record)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())

    def test_error_messages_no_secrets(self):
        try:
            raise DeviceInventoryError("test")
        except DeviceInventoryError as e:
            msg = str(e)
            self.assertNotIn("password", msg.lower())
            self.assertNotIn("secret", msg.lower())

    def test_service_no_secret_storage(self):
        service = DeviceInventoryService()
        for attr in ["password", "secret", "credential", "token"]:
            self.assertFalse(hasattr(service, attr))

    def test_devices_module_no_subprocess(self):
        import ast
        import os
        devices_dir = os.path.join("backup_manager", "devices")
        for filename in os.listdir(devices_dir):
            if not filename.endswith(".py"):
                continue
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

    def test_no_command_execution(self):
        """确认没有命令执行相关代码"""
        import ast
        import os
        devices_dir = os.path.join("backup_manager", "devices")
        for filename in os.listdir(devices_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(devices_dir, filename)
            with open(filepath) as f:
                src = f.read()
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() found in {filename}")


if __name__ == "__main__":
    unittest.main()
