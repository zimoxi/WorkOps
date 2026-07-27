"""
WorkOps Device Management Tests
Sprint077: Device Management Foundation

覆盖：
- DeviceType enum
- DeviceStatus enum
- Device model validation
- DeviceRegistry contract
- DeviceService contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.devices.models import DeviceType, DeviceStatus, Device
from backup_manager.devices.device_registry import DeviceRegistry
from backup_manager.devices.device_service import DeviceService
from backup_manager.devices.errors import (
    DeviceManagementError,
    DeviceNotFoundError,
    InvalidDeviceError,
)


# ============================================================================
# Helpers
# ============================================================================

NOW = datetime.now(timezone.utc)


def _make_device(**kwargs):
    defaults = {
        "device_id": "dev-001",
        "device_type": DeviceType.LINUX,
        "display_name": "Linux Server",
        "status": DeviceStatus.ONLINE,
        "created_at": NOW,
        "last_seen_at": NOW,
    }
    defaults.update(kwargs)
    return Device(**defaults)


# ============================================================================
# DeviceType
# ============================================================================

class TestDeviceType(unittest.TestCase):
    """设备类型测试"""

    def test_linux(self):
        self.assertEqual(DeviceType.LINUX.value, "linux")

    def test_pve(self):
        self.assertEqual(DeviceType.PVE.value, "pve")

    def test_omv(self):
        self.assertEqual(DeviceType.OMV.value, "omv")

    def test_three_types(self):
        self.assertEqual(len(DeviceType), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            DeviceType("nonexistent")


# ============================================================================
# DeviceStatus
# ============================================================================

class TestDeviceStatus(unittest.TestCase):
    """设备状态测试"""

    def test_online(self):
        self.assertEqual(DeviceStatus.ONLINE.value, "online")

    def test_offline(self):
        self.assertEqual(DeviceStatus.OFFLINE.value, "offline")

    def test_unknown(self):
        self.assertEqual(DeviceStatus.UNKNOWN.value, "unknown")

    def test_three_statuses(self):
        self.assertEqual(len(DeviceStatus), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            DeviceStatus("nonexistent")


# ============================================================================
# Device Model
# ============================================================================

class TestDeviceModel(unittest.TestCase):
    """设备模型测试"""

    def test_valid_device(self):
        device = _make_device()
        self.assertEqual(device.device_id, "dev-001")
        self.assertEqual(device.device_type, DeviceType.LINUX)
        self.assertEqual(device.display_name, "Linux Server")
        self.assertEqual(device.status, DeviceStatus.ONLINE)

    def test_frozen(self):
        device = _make_device()
        with self.assertRaises(AttributeError):
            device.device_id = "other"

    def test_slots(self):
        device = _make_device()
        with self.assertRaises(AttributeError):
            device.__dict__

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(device_id="")

    def test_invalid_device_type_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(device_type="linux")

    def test_empty_display_name_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(display_name="")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(status="online")

    def test_invalid_created_at_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(created_at="2025-01-01")

    def test_invalid_last_seen_at_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(last_seen_at="2025-01-01")

    def test_all_device_types(self):
        for dt in DeviceType:
            device = _make_device(device_type=dt)
            self.assertEqual(device.device_type, dt)

    def test_all_device_statuses(self):
        for ds in DeviceStatus:
            device = _make_device(status=ds)
            self.assertEqual(device.status, ds)

    def test_no_forbidden_fields(self):
        device = _make_device()
        for attr in ["password", "secret", "token", "credential", "private_key", "ssh_key"]:
            self.assertFalse(hasattr(device, attr))

    def test_repr_no_secrets(self):
        device = _make_device()
        r = repr(device)
        for term in ["password", "secret", "token", "credential", "private_key"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# DeviceRegistry Contract
# ============================================================================

class TestDeviceRegistryContract(unittest.TestCase):
    """设备注册表契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(DeviceRegistry, ABC))

    def test_has_register(self):
        self.assertTrue(hasattr(DeviceRegistry, "register"))

    def test_has_get(self):
        self.assertTrue(hasattr(DeviceRegistry, "get"))

    def test_has_list_all(self):
        self.assertTrue(hasattr(DeviceRegistry, "list_all"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            DeviceRegistry()

    def test_concrete_subclass(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        device = _make_device()
        registry.register(device)
        self.assertEqual(registry.get("dev-001").device_id, "dev-001")
        self.assertEqual(len(registry.list_all()), 1)

    def test_missing_register(self):
        class BadRegistry(DeviceRegistry):
            def get(self, device_id):
                pass
            def list_all(self):
                pass
        with self.assertRaises(TypeError):
            BadRegistry()

    def test_missing_get(self):
        class BadRegistry(DeviceRegistry):
            def register(self, device):
                pass
            def list_all(self):
                pass
        with self.assertRaises(TypeError):
            BadRegistry()

    def test_missing_list_all(self):
        class BadRegistry(DeviceRegistry):
            def register(self, device):
                pass
            def get(self, device_id):
                pass
        with self.assertRaises(TypeError):
            BadRegistry()


# ============================================================================
# DeviceService Contract
# ============================================================================

class TestDeviceServiceContract(unittest.TestCase):
    """设备服务契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(DeviceService, ABC))

    def test_has_register_device(self):
        self.assertTrue(hasattr(DeviceService, "register_device"))

    def test_has_list_devices(self):
        self.assertTrue(hasattr(DeviceService, "list_devices"))

    def test_has_get_device(self):
        self.assertTrue(hasattr(DeviceService, "get_device"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            DeviceService()

    def test_concrete_subclass(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        device = _make_device()
        service.register_device(device)
        self.assertEqual(len(service.list_devices()), 1)
        self.assertEqual(service.get_device("dev-001").device_id, "dev-001")

    def test_missing_register_device(self):
        class BadService(DeviceService):
            def list_devices(self):
                pass
            def get_device(self, device_id):
                pass
        with self.assertRaises(TypeError):
            BadService()

    def test_missing_list_devices(self):
        class BadService(DeviceService):
            def register_device(self, device):
                pass
            def get_device(self, device_id):
                pass
        with self.assertRaises(TypeError):
            BadService()

    def test_missing_get_device(self):
        class BadService(DeviceService):
            def register_device(self, device):
                pass
            def list_devices(self):
                pass
        with self.assertRaises(TypeError):
            BadService()


# ============================================================================
# Error Model
# ============================================================================

class TestDeviceManagementErrors(unittest.TestCase):
    """错误模型测试"""

    def test_management_error(self):
        with self.assertRaises(DeviceManagementError):
            raise DeviceManagementError("test")

    def test_not_found_error(self):
        with self.assertRaises(DeviceManagementError):
            raise DeviceNotFoundError("test")

    def test_invalid_device_error(self):
        with self.assertRaises(DeviceManagementError):
            raise InvalidDeviceError("test")

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(DeviceNotFoundError, DeviceManagementError))
        self.assertTrue(issubclass(InvalidDeviceError, DeviceManagementError))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (DeviceManagementError, ("test",)),
            (DeviceNotFoundError, ("test",)),
            (InvalidDeviceError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_device_no_credentials(self):
        device = _make_device()
        for attr in ["password", "secret", "token", "credential", "private_key", "ssh_key"]:
            self.assertFalse(hasattr(device, attr))

    def test_no_subprocess(self):
        import ast
        import os
        dev_dir = os.path.join("backup_manager", "devices")
        for filename in os.listdir(dev_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dev_dir, filename)
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
        dev_dir = os.path.join("backup_manager", "devices")
        for filename in os.listdir(dev_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(dev_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_full_lifecycle(self):
        """完整设备管理生命周期"""
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        class MockService(DeviceService):
            def __init__(self, registry):
                self._registry = registry
            def register_device(self, device):
                self._registry.register(device)
            def list_devices(self):
                return self._registry.list_all()
            def get_device(self, device_id):
                return self._registry.get(device_id)
        registry = MockRegistry()
        service = MockService(registry)
        for dt in DeviceType:
            device = _make_device(
                device_id=f"dev-{dt.value}",
                device_type=dt,
                display_name=f"{dt.value} device",
            )
            service.register_device(device)
        devices = service.list_devices()
        self.assertEqual(len(devices), 3)
        for d in devices:
            self.assertIsInstance(d, Device)


# ============================================================================
# Extended Tests
# ============================================================================

class TestDeviceManagementExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy_deep(self):
        self.assertTrue(issubclass(DeviceManagementError, Exception))
        self.assertTrue(issubclass(DeviceNotFoundError, Exception))
        self.assertTrue(issubclass(InvalidDeviceError, Exception))

    def test_device_preserves_all_fields(self):
        device = _make_device()
        self.assertEqual(device.device_id, "dev-001")
        self.assertEqual(device.device_type, DeviceType.LINUX)
        self.assertEqual(device.display_name, "Linux Server")
        self.assertEqual(device.status, DeviceStatus.ONLINE)
        self.assertEqual(device.created_at, NOW)
        self.assertEqual(device.last_seen_at, NOW)

    def test_device_repr_no_secrets(self):
        device = _make_device()
        r = repr(device)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_device_no_password(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "password"))

    def test_device_no_secret(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "secret"))

    def test_device_no_token(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "token"))

    def test_device_no_credential(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "credential"))

    def test_device_no_private_key(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "private_key"))

    def test_device_no_ssh_key(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "ssh_key"))

    def test_device_no_command(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "command"))

    def test_device_no_subprocess(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "subprocess"))

    def test_device_no_shell(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "shell"))

    def test_device_no_stdout(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "stdout"))

    def test_device_no_stderr(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "stderr"))

    def test_device_no_api_key(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "api_key"))

    def test_device_whitespace_id_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(device_id="   ")

    def test_device_whitespace_name_rejected(self):
        with self.assertRaises(InvalidDeviceError):
            _make_device(display_name="   ")

    def test_device_different_types(self):
        for dt in DeviceType:
            device = _make_device(device_type=dt, device_id=f"dev-{dt.value}")
            self.assertEqual(device.device_type, dt)

    def test_device_different_statuses(self):
        for ds in DeviceStatus:
            device = _make_device(status=ds)
            self.assertEqual(device.status, ds)

    def test_device_different_names(self):
        for name in ["Linux Server", "PVE Host", "OMV NAS", "Production"]:
            device = _make_device(display_name=name)
            self.assertEqual(device.display_name, name)

    def test_device_all_fields_present(self):
        device = _make_device()
        self.assertTrue(hasattr(device, "device_id"))
        self.assertTrue(hasattr(device, "device_type"))
        self.assertTrue(hasattr(device, "display_name"))
        self.assertTrue(hasattr(device, "status"))
        self.assertTrue(hasattr(device, "created_at"))
        self.assertTrue(hasattr(device, "last_seen_at"))

    def test_device_is_frozen_dataclass(self):
        device = _make_device()
        self.assertTrue(hasattr(device, '__dataclass_params__'))
        self.assertTrue(device.__dataclass_params__.frozen)

    def test_device_type_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(DeviceType, Enum))

    def test_device_status_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(DeviceStatus, Enum))

    def test_registry_register_get(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        device = _make_device()
        registry.register(device)
        result = registry.get("dev-001")
        self.assertEqual(result.device_id, "dev-001")

    def test_registry_get_not_found(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        result = registry.get("nonexistent")
        self.assertIsNone(result)

    def test_registry_list_empty(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        self.assertEqual(len(registry.list_all()), 0)

    def test_registry_list_multiple(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        for i in range(5):
            registry.register(_make_device(device_id=f"dev-{i:03d}"))
        self.assertEqual(len(registry.list_all()), 5)

    def test_service_register_list(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        device = _make_device()
        service.register_device(device)
        self.assertEqual(len(service.list_devices()), 1)

    def test_service_get_device(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        device = _make_device()
        service.register_device(device)
        result = service.get_device("dev-001")
        self.assertEqual(result.device_id, "dev-001")

    def test_service_get_not_found(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        result = service.get_device("nonexistent")
        self.assertIsNone(result)

    def test_service_register_all_types(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        for dt in DeviceType:
            service.register_device(_make_device(device_id=f"dev-{dt.value}", device_type=dt))
        self.assertEqual(len(service.list_devices()), 3)

    def test_error_messages_safe(self):
        try:
            raise DeviceManagementError("test")
        except DeviceManagementError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "credential", "private_key"]:
                self.assertNotIn(term, msg.lower())

    def test_not_found_error_message(self):
        exc = DeviceNotFoundError("device not found")
        self.assertIn("device not found", str(exc))

    def test_invalid_device_error_message(self):
        exc = InvalidDeviceError("invalid device")
        self.assertIn("invalid device", str(exc))

    def test_device_type_linux_value(self):
        self.assertEqual(DeviceType.LINUX.value, "linux")

    def test_device_type_pve_value(self):
        self.assertEqual(DeviceType.PVE.value, "pve")

    def test_device_type_omv_value(self):
        self.assertEqual(DeviceType.OMV.value, "omv")

    def test_device_status_online_value(self):
        self.assertEqual(DeviceStatus.ONLINE.value, "online")

    def test_device_status_offline_value(self):
        self.assertEqual(DeviceStatus.OFFLINE.value, "offline")

    def test_device_status_unknown_value(self):
        self.assertEqual(DeviceStatus.UNKNOWN.value, "unknown")

    def test_device_type_enum_members(self):
        self.assertEqual(len(list(DeviceType)), 3)

    def test_device_status_enum_members(self):
        self.assertEqual(len(list(DeviceStatus)), 3)

    def test_registry_register_returns_none(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        result = registry.register(_make_device())
        self.assertIsNone(result)

    def test_registry_list_returns_tuple(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        result = registry.list_all()
        self.assertIsInstance(result, tuple)

    def test_service_list_returns_tuple(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        result = service.list_devices()
        self.assertIsInstance(result, tuple)

    def test_device_created_at_timezone(self):
        device = _make_device()
        self.assertIsNotNone(device.created_at.tzinfo)

    def test_device_last_seen_at_timezone(self):
        device = _make_device()
        self.assertIsNotNone(device.last_seen_at.tzinfo)

    def test_device_invalid_type_device_id(self):
        with self.assertRaises(InvalidDeviceError):
            Device(
                device_id=123, device_type=DeviceType.LINUX,
                display_name="Linux", status=DeviceStatus.ONLINE,
                created_at=NOW, last_seen_at=NOW,
            )

    def test_device_invalid_type_display_name(self):
        with self.assertRaises(InvalidDeviceError):
            Device(
                device_id="dev-001", device_type=DeviceType.LINUX,
                display_name=123, status=DeviceStatus.ONLINE,
                created_at=NOW, last_seen_at=NOW,
            )

    def test_registry_register_multiple_same_type(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        for i in range(3):
            registry.register(_make_device(device_id=f"linux-{i:03d}", device_type=DeviceType.LINUX))
        self.assertEqual(len(registry.list_all()), 3)

    def test_registry_register_overwrites(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        registry.register(_make_device(display_name="Original"))
        registry.register(_make_device(display_name="Updated"))
        self.assertEqual(registry.get("dev-001").display_name, "Updated")

    def test_service_register_multiple(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        for i in range(10):
            service.register_device(_make_device(device_id=f"dev-{i:03d}"))
        self.assertEqual(len(service.list_devices()), 10)

    def test_device_all_statuses_with_all_types(self):
        for ds in DeviceStatus:
            for dt in DeviceType:
                device = _make_device(
                    device_id=f"dev-{dt.value}-{ds.value}",
                    device_type=dt,
                    status=ds,
                )
                self.assertEqual(device.device_type, dt)
                self.assertEqual(device.status, ds)

    def test_device_created_at_preserved(self):
        past = datetime(2024, 1, 1, tzinfo=timezone.utc)
        device = _make_device(created_at=past)
        self.assertEqual(device.created_at, past)

    def test_device_last_seen_at_preserved(self):
        past = datetime(2024, 6, 15, tzinfo=timezone.utc)
        device = _make_device(last_seen_at=past)
        self.assertEqual(device.last_seen_at, past)

    def test_registry_get_returns_device(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        device = _make_device()
        registry.register(device)
        result = registry.get("dev-001")
        self.assertIsInstance(result, Device)

    def test_service_get_returns_device(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        device = _make_device()
        service.register_device(device)
        result = service.get_device("dev-001")
        self.assertIsInstance(result, Device)

    def test_device_no_forbidden_attrs_extra(self):
        device = _make_device()
        for attr in ["password", "secret", "token", "credential", "private_key", "ssh_key", "command", "subprocess", "shell", "stdout", "stderr", "api_key"]:
            self.assertFalse(hasattr(device, attr))

    def test_error_hierarchy_all_subclasses(self):
        subclasses = [DeviceNotFoundError, InvalidDeviceError]
        for cls in subclasses:
            self.assertTrue(issubclass(cls, DeviceManagementError))

    def test_device_type_is_enum_member(self):
        for dt in DeviceType:
            self.assertIsInstance(dt.value, str)

    def test_device_status_is_enum_member(self):
        for ds in DeviceStatus:
            self.assertIsInstance(ds.value, str)

    def test_registry_list_returns_tuple_of_devices(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        registry.register(_make_device())
        result = registry.list_all()
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], Device)

    def test_service_list_returns_tuple_of_devices(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        service.register_device(_make_device())
        result = service.list_devices()
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result[0], Device)

    def test_device_multiple_registrations(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        service.register_device(_make_device(device_id="dev-001", device_type=DeviceType.LINUX))
        service.register_device(_make_device(device_id="dev-002", device_type=DeviceType.PVE))
        service.register_device(_make_device(device_id="dev-003", device_type=DeviceType.OMV))
        self.assertEqual(len(service.list_devices()), 3)
        self.assertEqual(service.get_device("dev-001").device_type, DeviceType.LINUX)
        self.assertEqual(service.get_device("dev-002").device_type, DeviceType.PVE)
        self.assertEqual(service.get_device("dev-003").device_type, DeviceType.OMV)

    def test_service_register_returns_none(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        result = service.register_device(_make_device())
        self.assertIsNone(result)

    def test_device_type_members(self):
        members = list(DeviceType)
        self.assertEqual(len(members), 3)

    def test_device_status_members(self):
        members = list(DeviceStatus)
        self.assertEqual(len(members), 3)

    def test_registry_register_empty_list(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        self.assertEqual(len(registry.list_all()), 0)

    def test_service_list_empty(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        self.assertEqual(len(service.list_devices()), 0)

    def test_device_offline_status(self):
        device = _make_device(status=DeviceStatus.OFFLINE)
        self.assertEqual(device.status, DeviceStatus.OFFLINE)

    def test_device_unknown_status(self):
        device = _make_device(status=DeviceStatus.UNKNOWN)
        self.assertEqual(device.status, DeviceStatus.UNKNOWN)

    def test_device_pve_type(self):
        device = _make_device(device_type=DeviceType.PVE, device_id="pve-001")
        self.assertEqual(device.device_type, DeviceType.PVE)

    def test_device_omv_type(self):
        device = _make_device(device_type=DeviceType.OMV, device_id="omv-001")
        self.assertEqual(device.device_type, DeviceType.OMV)

    def test_registry_multiple_gets(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        for i in range(5):
            registry.register(_make_device(device_id=f"dev-{i:03d}"))
        for i in range(5):
            result = registry.get(f"dev-{i:03d}")
            self.assertIsNotNone(result)

    def test_service_multiple_gets(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        for i in range(5):
            service.register_device(_make_device(device_id=f"dev-{i:03d}"))
        for i in range(5):
            result = service.get_device(f"dev-{i:03d}")
            self.assertIsNotNone(result)

    def test_device_preserves_timestamps(self):
        t1 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        t2 = datetime(2024, 6, 15, 18, 30, 0, tzinfo=timezone.utc)
        device = _make_device(created_at=t1, last_seen_at=t2)
        self.assertEqual(device.created_at, t1)
        self.assertEqual(device.last_seen_at, t2)

    def test_device_same_timestamps(self):
        device = _make_device(created_at=NOW, last_seen_at=NOW)
        self.assertEqual(device.created_at, device.last_seen_at)

    def test_error_not_found_message(self):
        exc = DeviceNotFoundError("dev-001 not found")
        self.assertIn("dev-001 not found", str(exc))

    def test_error_invalid_message(self):
        exc = InvalidDeviceError("invalid device_id")
        self.assertIn("invalid device_id", str(exc))

    def test_error_management_message(self):
        exc = DeviceManagementError("generic error")
        self.assertIn("generic error", str(exc))

    def test_registry_register_preserves_type(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        for dt in DeviceType:
            registry.register(_make_device(device_id=f"dev-{dt.value}", device_type=dt))
        for dt in DeviceType:
            result = registry.get(f"dev-{dt.value}")
            self.assertEqual(result.device_type, dt)

    def test_service_register_preserves_status(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        for ds in DeviceStatus:
            service.register_device(_make_device(device_id=f"dev-{ds.value}", status=ds))
        for ds in DeviceStatus:
            result = service.get_device(f"dev-{ds.value}")
            self.assertEqual(result.status, ds)

    def test_device_is_frozen_check(self):
        device = _make_device()
        self.assertTrue(device.__dataclass_params__.frozen)

    def test_device_has_slots(self):
        device = _make_device()
        with self.assertRaises(AttributeError):
            device.__dict__

    def test_registry_contract_methods(self):
        self.assertTrue(hasattr(DeviceRegistry, "register"))
        self.assertTrue(hasattr(DeviceRegistry, "get"))
        self.assertTrue(hasattr(DeviceRegistry, "list_all"))

    def test_service_contract_methods(self):
        self.assertTrue(hasattr(DeviceService, "register_device"))
        self.assertTrue(hasattr(DeviceService, "list_devices"))
        self.assertTrue(hasattr(DeviceService, "get_device"))

    def test_device_display_name_preserved(self):
        names = ["Linux Server", "PVE Host", "OMV NAS", "Production", "Staging", "Dev"]
        for name in names:
            device = _make_device(display_name=name)
            self.assertEqual(device.display_name, name)

    def test_device_id_preserved(self):
        ids = ["dev-001", "dev-002", "linux-ssh-01", "pve-api-01", "omv-01"]
        for did in ids:
            device = _make_device(device_id=did)
            self.assertEqual(device.device_id, did)

    def test_registry_get_none_for_missing(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        self.assertIsNone(registry.get("nonexistent"))
        self.assertIsNone(registry.get(""))
        self.assertIsNone(registry.get("dev-999"))

    def test_service_get_none_for_missing(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        self.assertIsNone(service.get_device("nonexistent"))

    def test_device_all_types_enum(self):
        self.assertIn(DeviceType.LINUX, DeviceType)
        self.assertIn(DeviceType.PVE, DeviceType)
        self.assertIn(DeviceType.OMV, DeviceType)

    def test_device_all_statuses_enum(self):
        self.assertIn(DeviceStatus.ONLINE, DeviceStatus)
        self.assertIn(DeviceStatus.OFFLINE, DeviceStatus)
        self.assertIn(DeviceStatus.UNKNOWN, DeviceStatus)

    def test_registry_list_returns_tuple_type(self):
        class MockRegistry(DeviceRegistry):
            def __init__(self):
                self._devices = {}
            def register(self, device):
                self._devices[device.device_id] = device
            def get(self, device_id):
                return self._devices.get(device_id)
            def list_all(self):
                return tuple(self._devices.values())
        registry = MockRegistry()
        self.assertIsInstance(registry.list_all(), tuple)

    def test_service_list_returns_tuple_type(self):
        class MockService(DeviceService):
            def __init__(self):
                self._devices = {}
            def register_device(self, device):
                self._devices[device.device_id] = device
            def list_devices(self):
                return tuple(self._devices.values())
            def get_device(self, device_id):
                return self._devices.get(device_id)
        service = MockService()
        self.assertIsInstance(service.list_devices(), tuple)

    def test_device_no_forbidden_extra(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "password"))
        self.assertFalse(hasattr(device, "secret"))
        self.assertFalse(hasattr(device, "token"))
        self.assertFalse(hasattr(device, "credential"))
        self.assertFalse(hasattr(device, "private_key"))
        self.assertFalse(hasattr(device, "ssh_key"))
        self.assertFalse(hasattr(device, "command"))
        self.assertFalse(hasattr(device, "subprocess"))
        self.assertFalse(hasattr(device, "shell"))
        self.assertFalse(hasattr(device, "stdout"))
        self.assertFalse(hasattr(device, "stderr"))
        self.assertFalse(hasattr(device, "api_key"))

    def test_error_hierarchy_management(self):
        self.assertTrue(issubclass(DeviceManagementError, Exception))

    def test_error_hierarchy_not_found(self):
        self.assertTrue(issubclass(DeviceNotFoundError, Exception))

    def test_error_hierarchy_invalid(self):
        self.assertTrue(issubclass(InvalidDeviceError, Exception))

    def test_device_management_error_is_exception(self):
        exc = DeviceManagementError("test")
        self.assertIsInstance(exc, Exception)


if __name__ == "__main__":
    unittest.main()
