"""
WorkOps Runtime Health Probe Tests
Sprint076: Runtime Health Probe and Device Inventory

覆盖：
- RuntimeHealthStatus enum
- RuntimeDevice validation
- RuntimeHealthResult validation
- RuntimeHealthProbe contract
- RuntimeInventory contract
- RuntimeHealthService contract
- Error model
- Security boundary
"""

import unittest

from backup_manager.health_runtime.health_models import (
    RuntimeHealthStatus,
    RuntimeDevice,
    RuntimeHealthResult,
)
from backup_manager.health_runtime.probe import RuntimeHealthProbe
from backup_manager.health_runtime.inventory import RuntimeInventory
from backup_manager.health_runtime.service import RuntimeHealthService
from backup_manager.health_runtime.errors import (
    HealthRuntimeError,
    ProbeUnavailableError,
    InvalidRuntimeDeviceError,
    HealthRuntimeUnavailableError,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_device(**kwargs):
    defaults = {
        "device_id": "dev-001",
        "device_type": "linux_ssh",
        "display_name": "Linux Server",
        "status": RuntimeHealthStatus.HEALTHY,
    }
    defaults.update(kwargs)
    return RuntimeDevice(**defaults)


def _make_health_result(**kwargs):
    defaults = {
        "device_id": "dev-001",
        "status": RuntimeHealthStatus.HEALTHY,
        "message": "ok",
    }
    defaults.update(kwargs)
    return RuntimeHealthResult(**defaults)


# ============================================================================
# RuntimeHealthStatus
# ============================================================================

class TestRuntimeHealthStatus(unittest.TestCase):
    """运行时健康状态测试"""

    def test_healthy(self):
        self.assertEqual(RuntimeHealthStatus.HEALTHY.value, "healthy")

    def test_degraded(self):
        self.assertEqual(RuntimeHealthStatus.DEGRADED.value, "degraded")

    def test_unavailable(self):
        self.assertEqual(RuntimeHealthStatus.UNAVAILABLE.value, "unavailable")

    def test_three_statuses(self):
        self.assertEqual(len(RuntimeHealthStatus), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RuntimeHealthStatus("nonexistent")


# ============================================================================
# RuntimeDevice
# ============================================================================

class TestRuntimeDevice(unittest.TestCase):
    """运行时设备测试"""

    def test_valid_device(self):
        device = _make_device()
        self.assertEqual(device.device_id, "dev-001")
        self.assertEqual(device.device_type, "linux_ssh")
        self.assertEqual(device.display_name, "Linux Server")
        self.assertEqual(device.status, RuntimeHealthStatus.HEALTHY)

    def test_frozen(self):
        device = _make_device()
        with self.assertRaises(AttributeError):
            device.device_id = "other"

    def test_slots(self):
        device = _make_device()
        with self.assertRaises(AttributeError):
            device.__dict__

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(device_id="")

    def test_empty_device_type_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(device_type="")

    def test_empty_display_name_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(display_name="")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(status="healthy")

    def test_timezone_aware(self):
        device = _make_device()
        self.assertIsNotNone(device.checked_at.tzinfo)

    def test_all_statuses(self):
        for status in RuntimeHealthStatus:
            device = _make_device(status=status)
            self.assertEqual(device.status, status)

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
# RuntimeHealthResult
# ============================================================================

class TestRuntimeHealthResult(unittest.TestCase):
    """运行时健康检查结果测试"""

    def test_valid_result(self):
        result = _make_health_result()
        self.assertEqual(result.device_id, "dev-001")
        self.assertEqual(result.status, RuntimeHealthStatus.HEALTHY)
        self.assertEqual(result.message, "ok")

    def test_frozen(self):
        result = _make_health_result()
        with self.assertRaises(AttributeError):
            result.device_id = "other"

    def test_slots(self):
        result = _make_health_result()
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_device_id_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_health_result(device_id="")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_health_result(status="healthy")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeHealthResult(
                device_id="dev-001", status=RuntimeHealthStatus.HEALTHY,
                message=123,
            )

    def test_timezone_aware(self):
        result = _make_health_result()
        self.assertIsNotNone(result.checked_at.tzinfo)

    def test_all_statuses(self):
        for status in RuntimeHealthStatus:
            result = _make_health_result(status=status)
            self.assertEqual(result.status, status)

    def test_no_forbidden_fields(self):
        result = _make_health_result()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# RuntimeHealthProbe Contract
# ============================================================================

class TestRuntimeHealthProbeContract(unittest.TestCase):
    """运行时健康探针契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RuntimeHealthProbe, ABC))

    def test_has_check(self):
        self.assertTrue(hasattr(RuntimeHealthProbe, "check"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RuntimeHealthProbe()

    def test_concrete_subclass(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        device = _make_device()
        result = probe.check(device)
        self.assertEqual(result.status, RuntimeHealthStatus.HEALTHY)

    def test_missing_check(self):
        class BadProbe(RuntimeHealthProbe):
            pass
        with self.assertRaises(TypeError):
            BadProbe()


# ============================================================================
# RuntimeInventory Contract
# ============================================================================

class TestRuntimeInventoryContract(unittest.TestCase):
    """运行时设备清单契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RuntimeInventory, ABC))

    def test_has_list_devices(self):
        self.assertTrue(hasattr(RuntimeInventory, "list_devices"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RuntimeInventory()

    def test_concrete_subclass(self):
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return (
                    _make_device(),
                    _make_device(device_id="dev-002", device_type="pve_api", display_name="PVE Host"),
                )
        inventory = MockInventory()
        devices = inventory.list_devices()
        self.assertEqual(len(devices), 2)

    def test_missing_list_devices(self):
        class BadInventory(RuntimeInventory):
            pass
        with self.assertRaises(TypeError):
            BadInventory()


# ============================================================================
# RuntimeHealthService Contract
# ============================================================================

class TestRuntimeHealthServiceContract(unittest.TestCase):
    """运行时健康服务契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RuntimeHealthService, ABC))

    def test_has_check_all(self):
        self.assertTrue(hasattr(RuntimeHealthService, "check_all"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RuntimeHealthService()

    def test_concrete_subclass(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [_make_health_result()]
        service = MockService()
        results = service.check_all()
        self.assertEqual(len(results), 1)

    def test_missing_check_all(self):
        class BadService(RuntimeHealthService):
            pass
        with self.assertRaises(TypeError):
            BadService()


# ============================================================================
# Error Model
# ============================================================================

class TestHealthRuntimeErrors(unittest.TestCase):
    """错误模型测试"""

    def test_health_runtime_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise HealthRuntimeError("test")

    def test_probe_unavailable_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise ProbeUnavailableError("test")

    def test_invalid_device_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise InvalidRuntimeDeviceError("test")

    def test_unavailable_error(self):
        with self.assertRaises(HealthRuntimeError):
            raise HealthRuntimeUnavailableError("test")

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(ProbeUnavailableError, HealthRuntimeError))
        self.assertTrue(issubclass(InvalidRuntimeDeviceError, HealthRuntimeError))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (HealthRuntimeError, ("test",)),
            (ProbeUnavailableError, ("test",)),
            (InvalidRuntimeDeviceError, ("test",)),
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

    def test_result_no_credentials(self):
        result = _make_health_result()
        for attr in ["password", "secret", "token", "credential", "private_key"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        hr_dir = os.path.join("backup_manager", "health_runtime")
        for filename in ["health_models.py", "probe.py", "inventory.py", "service.py"]:
            filepath = os.path.join(hr_dir, filename)
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
        hr_dir = os.path.join("backup_manager", "health_runtime")
        for filename in ["health_models.py", "probe.py", "inventory.py", "service.py"]:
            filepath = os.path.join(hr_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_full_lifecycle(self):
        """完整健康检查生命周期"""
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return (
                    _make_device(device_id="dev-001", device_type="linux_ssh", display_name="Linux"),
                    _make_device(device_id="dev-002", device_type="pve_api", display_name="PVE"),
                    _make_device(device_id="dev-003", device_type="omv_api", display_name="OMV"),
                )
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        class MockService(RuntimeHealthService):
            def __init__(self, inventory, probe):
                self._inventory = inventory
                self._probe = probe
            def check_all(self):
                devices = self._inventory.list_devices()
                return [self._probe.check(d) for d in devices]
        inventory = MockInventory()
        probe = MockProbe()
        service = MockService(inventory, probe)
        results = service.check_all()
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertEqual(r.status, RuntimeHealthStatus.HEALTHY)


# ============================================================================
# Extended Tests
# ============================================================================

class TestRuntimeHealthProbeExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy_deep(self):
        self.assertTrue(issubclass(HealthRuntimeError, Exception))
        self.assertTrue(issubclass(ProbeUnavailableError, Exception))
        self.assertTrue(issubclass(InvalidRuntimeDeviceError, Exception))

    def test_device_preserves_all_fields(self):
        device = _make_device()
        self.assertEqual(device.device_id, "dev-001")
        self.assertEqual(device.device_type, "linux_ssh")
        self.assertEqual(device.display_name, "Linux Server")
        self.assertEqual(device.status, RuntimeHealthStatus.HEALTHY)

    def test_result_preserves_all_fields(self):
        result = _make_health_result()
        self.assertEqual(result.device_id, "dev-001")
        self.assertEqual(result.status, RuntimeHealthStatus.HEALTHY)
        self.assertEqual(result.message, "ok")

    def test_device_repr_no_secrets(self):
        device = _make_device()
        r = repr(device)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = _make_health_result()
        r = repr(result)
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

    def test_result_no_password(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "password"))

    def test_result_no_secret(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "secret"))

    def test_result_no_token(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "token"))

    def test_result_no_credential(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "credential"))

    def test_result_no_private_key(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "private_key"))

    def test_device_whitespace_id_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(device_id="   ")

    def test_device_whitespace_type_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(device_type="   ")

    def test_device_whitespace_name_rejected(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            _make_device(display_name="   ")

    def test_result_empty_message_accepted(self):
        result = RuntimeHealthResult(
            device_id="dev-001", status=RuntimeHealthStatus.HEALTHY,
            message="",
        )
        self.assertEqual(result.message, "")

    def test_device_different_types(self):
        for dt in ["linux_ssh", "pve_api", "omv_api"]:
            device = _make_device(device_type=dt)
            self.assertEqual(device.device_type, dt)

    def test_device_different_statuses(self):
        for status in RuntimeHealthStatus:
            device = _make_device(status=status)
            self.assertEqual(device.status, status)

    def test_result_different_statuses(self):
        for status in RuntimeHealthStatus:
            result = _make_health_result(status=status)
            self.assertEqual(result.status, status)

    def test_probe_returns_result(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        result = probe.check(_make_device())
        self.assertIsInstance(result, RuntimeHealthResult)

    def test_inventory_returns_tuple(self):
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return (_make_device(),)
        inventory = MockInventory()
        devices = inventory.list_devices()
        self.assertIsInstance(devices, tuple)

    def test_service_returns_list(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [_make_health_result()]
        service = MockService()
        results = service.check_all()
        self.assertIsInstance(results, list)

    def test_device_all_fields_present(self):
        device = _make_device()
        self.assertTrue(hasattr(device, "device_id"))
        self.assertTrue(hasattr(device, "device_type"))
        self.assertTrue(hasattr(device, "display_name"))
        self.assertTrue(hasattr(device, "status"))
        self.assertTrue(hasattr(device, "checked_at"))

    def test_result_all_fields_present(self):
        result = _make_health_result()
        self.assertTrue(hasattr(result, "device_id"))
        self.assertTrue(hasattr(result, "status"))
        self.assertTrue(hasattr(result, "message"))
        self.assertTrue(hasattr(result, "checked_at"))

    def test_device_is_frozen_dataclass(self):
        device = _make_device()
        self.assertTrue(hasattr(device, '__dataclass_params__'))
        self.assertTrue(device.__dataclass_params__.frozen)

    def test_result_is_frozen_dataclass(self):
        result = _make_health_result()
        self.assertTrue(hasattr(result, '__dataclass_params__'))
        self.assertTrue(result.__dataclass_params__.frozen)

    def test_health_status_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(RuntimeHealthStatus, Enum))

    def test_device_checked_at_type(self):
        from datetime import datetime
        device = _make_device()
        self.assertIsInstance(device.checked_at, datetime)

    def test_result_checked_at_type(self):
        from datetime import datetime
        result = _make_health_result()
        self.assertIsInstance(result.checked_at, datetime)

    def test_device_no_command(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "command"))

    def test_device_no_subprocess(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "subprocess"))

    def test_device_no_shell(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "shell"))

    def test_result_no_command(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "command"))

    def test_result_no_ssh(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "ssh"))

    def test_probe_multiple_devices(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        for i in range(5):
            device = _make_device(device_id=f"dev-{i:03d}")
            result = probe.check(device)
            self.assertEqual(result.device_id, f"dev-{i:03d}")

    def test_inventory_empty(self):
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return ()
        inventory = MockInventory()
        devices = inventory.list_devices()
        self.assertEqual(len(devices), 0)

    def test_service_check_all_returns_results(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [
                    _make_health_result(device_id="dev-001"),
                    _make_health_result(device_id="dev-002"),
                    _make_health_result(device_id="dev-003"),
                ]
        service = MockService()
        results = service.check_all()
        self.assertEqual(len(results), 3)

    def test_service_degraded_result(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [_make_health_result(status=RuntimeHealthStatus.DEGRADED, message="slow")]
        service = MockService()
        results = service.check_all()
        self.assertEqual(results[0].status, RuntimeHealthStatus.DEGRADED)

    def test_service_unavailable_result(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [_make_health_result(status=RuntimeHealthStatus.UNAVAILABLE, message="down")]
        service = MockService()
        results = service.check_all()
        self.assertEqual(results[0].status, RuntimeHealthStatus.UNAVAILABLE)

    def test_probe_unavailable_error_message(self):
        exc = ProbeUnavailableError("probe down")
        self.assertIn("probe down", str(exc))

    def test_invalid_device_error_message(self):
        exc = InvalidRuntimeDeviceError("invalid device")
        self.assertIn("invalid device", str(exc))

    def test_unavailable_error_message(self):
        exc = HealthRuntimeUnavailableError("unavailable")
        self.assertIn("unavailable", str(exc))

    def test_device_invalid_type_device_id(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeDevice(device_id=123, device_type="linux_ssh", display_name="Linux", status=RuntimeHealthStatus.HEALTHY)

    def test_device_invalid_type_device_type(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeDevice(device_id="dev-001", device_type=123, display_name="Linux", status=RuntimeHealthStatus.HEALTHY)

    def test_device_invalid_type_display_name(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeDevice(device_id="dev-001", device_type="linux_ssh", display_name=123, status=RuntimeHealthStatus.HEALTHY)

    def test_result_invalid_type_device_id(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeHealthResult(device_id=123, status=RuntimeHealthStatus.HEALTHY, message="ok")

    def test_result_invalid_type_status(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeHealthResult(device_id="dev-001", status="healthy", message="ok")

    def test_result_invalid_type_message(self):
        with self.assertRaises(InvalidRuntimeDeviceError):
            RuntimeHealthResult(device_id="dev-001", status=RuntimeHealthStatus.HEALTHY, message=123)

    def test_device_multiple_types(self):
        for dt in ["linux_ssh", "pve_api", "omv_api"]:
            device = _make_device(device_id=f"dev-{dt}", device_type=dt, display_name=f"Device {dt}")
            self.assertEqual(device.device_type, dt)

    def test_device_multiple_names(self):
        for name in ["Linux Server", "PVE Host", "OMV NAS", "Production Server"]:
            device = _make_device(display_name=name)
            self.assertEqual(device.display_name, name)

    def test_result_multiple_messages(self):
        for msg in ["ok", "slow response", "connection refused", "timeout"]:
            result = _make_health_result(message=msg)
            self.assertEqual(result.message, msg)

    def test_probe_healthy(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        result = probe.check(_make_device())
        self.assertEqual(result.status, RuntimeHealthStatus.HEALTHY)

    def test_probe_degraded(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.DEGRADED,
                    message="slow",
                )
        probe = MockProbe()
        result = probe.check(_make_device())
        self.assertEqual(result.status, RuntimeHealthStatus.DEGRADED)

    def test_probe_unavailable(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.UNAVAILABLE,
                    message="down",
                )
        probe = MockProbe()
        result = probe.check(_make_device())
        self.assertEqual(result.status, RuntimeHealthStatus.UNAVAILABLE)

    def test_inventory_multiple_devices(self):
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return tuple(
                    _make_device(device_id=f"dev-{i:03d}")
                    for i in range(10)
                )
        inventory = MockInventory()
        devices = inventory.list_devices()
        self.assertEqual(len(devices), 10)

    def test_service_empty_results(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return []
        service = MockService()
        results = service.check_all()
        self.assertEqual(len(results), 0)

    def test_service_mixed_statuses(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [
                    _make_health_result(device_id="dev-001", status=RuntimeHealthStatus.HEALTHY),
                    _make_health_result(device_id="dev-002", status=RuntimeHealthStatus.DEGRADED),
                    _make_health_result(device_id="dev-003", status=RuntimeHealthStatus.UNAVAILABLE),
                ]
        service = MockService()
        results = service.check_all()
        self.assertEqual(results[0].status, RuntimeHealthStatus.HEALTHY)
        self.assertEqual(results[1].status, RuntimeHealthStatus.DEGRADED)
        self.assertEqual(results[2].status, RuntimeHealthStatus.UNAVAILABLE)

    def test_device_no_stdout(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "stdout"))

    def test_device_no_stderr(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "stderr"))

    def test_result_no_stdout(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "stdout"))

    def test_result_no_stderr(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "stderr"))

    def test_device_no_api_key(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "api_key"))

    def test_result_no_api_key(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "api_key"))

    def test_device_no_command(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "command"))

    def test_result_no_command(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "command"))

    def test_probe_check_returns_result_type(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        result = probe.check(_make_device())
        self.assertIsInstance(result, RuntimeHealthResult)

    def test_inventory_list_returns_tuple_type(self):
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return (_make_device(),)
        inventory = MockInventory()
        devices = inventory.list_devices()
        self.assertIsInstance(devices, tuple)

    def test_service_check_all_returns_list_type(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [_make_health_result()]
        service = MockService()
        results = service.check_all()
        self.assertIsInstance(results, list)

    def test_status_healthy_value(self):
        self.assertEqual(RuntimeHealthStatus.HEALTHY.value, "healthy")

    def test_status_degraded_value(self):
        self.assertEqual(RuntimeHealthStatus.DEGRADED.value, "degraded")

    def test_status_unavailable_value(self):
        self.assertEqual(RuntimeHealthStatus.UNAVAILABLE.value, "unavailable")

    def test_device_id_preserved_in_result(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        device = _make_device(device_id="custom-id-123")
        result = probe.check(device)
        self.assertEqual(result.device_id, "custom-id-123")

    def test_probe_multiple_calls(self):
        class MockProbe(RuntimeHealthProbe):
            def __init__(self):
                self.call_count = 0
            def check(self, device):
                self.call_count += 1
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        for i in range(5):
            probe.check(_make_device(device_id=f"dev-{i:03d}"))
        self.assertEqual(probe.call_count, 5)

    def test_service_multiple_calls(self):
        class MockService(RuntimeHealthService):
            def __init__(self):
                self.call_count = 0
            def check_all(self):
                self.call_count += 1
                return [_make_health_result()]
        service = MockService()
        for _ in range(5):
            service.check_all()
        self.assertEqual(service.call_count, 5)

    def test_device_result_same_device_id(self):
        device = _make_device(device_id="dev-abc")
        result = RuntimeHealthResult(
            device_id=device.device_id,
            status=device.status,
            message="ok",
        )
        self.assertEqual(device.device_id, result.device_id)

    def test_error_probe_unavailable_message(self):
        exc = ProbeUnavailableError("probe timeout")
        self.assertIn("probe timeout", str(exc))

    def test_error_invalid_device_message(self):
        exc = InvalidRuntimeDeviceError("missing device_id")
        self.assertIn("missing device_id", str(exc))

    def test_error_unavailable_message(self):
        exc = HealthRuntimeUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_error_health_runtime_message(self):
        exc = HealthRuntimeError("generic error")
        self.assertIn("generic error", str(exc))

    def test_device_no_private_key_field(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "private_key"))

    def test_result_no_private_key_field(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "private_key"))

    def test_device_no_ssh_key_field(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "ssh_key"))

    def test_result_no_ssh_key_field(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "ssh_key"))

    def test_device_no_subprocess_field(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "subprocess"))

    def test_result_no_subprocess_field(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "subprocess"))

    def test_device_no_shell_field(self):
        device = _make_device()
        self.assertFalse(hasattr(device, "shell"))

    def test_result_no_shell_field(self):
        result = _make_health_result()
        self.assertFalse(hasattr(result, "shell"))

    def test_probe_check_preserves_device_id(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="ok",
                )
        probe = MockProbe()
        for did in ["dev-001", "dev-002", "dev-abc", "linux-ssh-01"]:
            device = _make_device(device_id=did)
            result = probe.check(device)
            self.assertEqual(result.device_id, did)

    def test_inventory_returns_devices(self):
        class MockInventory(RuntimeInventory):
            def list_devices(self):
                return (
                    _make_device(device_id="dev-001", device_type="linux_ssh"),
                    _make_device(device_id="dev-002", device_type="pve_api"),
                    _make_device(device_id="dev-003", device_type="omv_api"),
                )
        inventory = MockInventory()
        devices = inventory.list_devices()
        self.assertEqual(len(devices), 3)
        self.assertEqual(devices[0].device_type, "linux_ssh")
        self.assertEqual(devices[1].device_type, "pve_api")
        self.assertEqual(devices[2].device_type, "omv_api")

    def test_service_check_all_with_3_devices(self):
        class MockService(RuntimeHealthService):
            def check_all(self):
                return [
                    _make_health_result(device_id="dev-001", status=RuntimeHealthStatus.HEALTHY),
                    _make_health_result(device_id="dev-002", status=RuntimeHealthStatus.HEALTHY),
                    _make_health_result(device_id="dev-003", status=RuntimeHealthStatus.HEALTHY),
                ]
        service = MockService()
        results = service.check_all()
        self.assertEqual(len(results), 3)
        for r in results:
            self.assertEqual(r.status, RuntimeHealthStatus.HEALTHY)

    def test_probe_result_message_preserved(self):
        class MockProbe(RuntimeHealthProbe):
            def check(self, device):
                return RuntimeHealthResult(
                    device_id=device.device_id,
                    status=RuntimeHealthStatus.HEALTHY,
                    message="all systems operational",
                )
        probe = MockProbe()
        result = probe.check(_make_device())
        self.assertEqual(result.message, "all systems operational")

    def test_device_created_at_type(self):
        from datetime import datetime
        device = _make_device()
        self.assertIsInstance(device.checked_at, datetime)

    def test_result_created_at_type(self):
        from datetime import datetime
        result = _make_health_result()
        self.assertIsInstance(result.checked_at, datetime)

    def test_error_hierarchy_all_subclasses(self):
        subclasses = [ProbeUnavailableError, InvalidRuntimeDeviceError]
        for cls in subclasses:
            self.assertTrue(issubclass(cls, HealthRuntimeError))

    def test_status_enum_members(self):
        members = list(RuntimeHealthStatus)
        self.assertEqual(len(members), 3)

    def test_device_is_frozen(self):
        device = _make_device()
        self.assertTrue(device.__dataclass_params__.frozen)

    def test_result_is_frozen(self):
        result = _make_health_result()
        self.assertTrue(result.__dataclass_params__.frozen)


if __name__ == "__main__":
    unittest.main()
