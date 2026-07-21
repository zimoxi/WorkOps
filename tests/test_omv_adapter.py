"""
WorkOps OMV Adapter Tests
Sprint028: OMV ReadOnly Adapter

覆盖：
- OMVAdapter initialization
- Capability declaration
- Registry integration
- Client contract
- Result models
- Readonly boundary
- Security checks
"""

import unittest

from backup_manager.adapters.omv_adapter import OMVAdapter, OMV_CAPABILITIES
from backup_manager.adapters.omv import (
    OMVAdapterError,
    OMVQueryError,
    OMVUnsupportedOperationError,
    OMVSystemInfo,
    OMVStorageInfo,
    OMVStatus,
    OMVClient,
)
from backup_manager.adapters.capability import AdapterCapabilityDeclaration
from backup_manager.adapters.capability_registry import AdapterCapabilityRegistry
from backup_manager.adapters.errors import AdapterNotConnectedError
from backup_manager.devices.capability import DeviceCapability


# ============================================================================
# OMVAdapter Initialization
# ============================================================================

class TestOMVAdapterInit(unittest.TestCase):
    """适配器初始化测试"""

    def test_adapter_type(self):
        adapter = OMVAdapter()
        self.assertEqual(adapter.adapter_type, "omv")

    def test_not_connected_by_default(self):
        adapter = OMVAdapter()
        self.assertFalse(adapter._connected)

    def test_connect(self):
        adapter = OMVAdapter()
        result = adapter.connect({})
        self.assertTrue(result)
        self.assertTrue(adapter._connected)

    def test_disconnect(self):
        adapter = OMVAdapter()
        adapter.connect({})
        adapter.disconnect()
        self.assertFalse(adapter._connected)

    def test_no_forbidden_methods(self):
        adapter = OMVAdapter()
        for method in ["modify_filesystem", "configure_smb", "configure_nfs",
                       "modify_raid", "create_user", "delete_user"]:
            self.assertFalse(
                hasattr(adapter, method),
                f"OMVAdapter should not have {method}"
            )


# ============================================================================
# Capability Declaration
# ============================================================================

class TestOMVCapabilityDeclaration(unittest.TestCase):
    """能力声明测试"""

    def test_capability_count(self):
        self.assertEqual(len(OMV_CAPABILITIES), 4)

    def test_system_info(self):
        self.assertIn(DeviceCapability.SYSTEM_INFO, OMV_CAPABILITIES)

    def test_status_query(self):
        self.assertIn(DeviceCapability.STATUS_QUERY, OMV_CAPABILITIES)

    def test_storage_query(self):
        self.assertIn(DeviceCapability.STORAGE_QUERY, OMV_CAPABILITIES)

    def test_backup_target(self):
        self.assertIn(DeviceCapability.BACKUP_TARGET, OMV_CAPABILITIES)

    def test_no_backup_source(self):
        self.assertNotIn(DeviceCapability.BACKUP_SOURCE, OMV_CAPABILITIES)

    def test_declaration_method(self):
        decl = OMVAdapter.capability_declaration()
        self.assertIsInstance(decl, AdapterCapabilityDeclaration)
        self.assertEqual(decl.adapter_type, "omv")

    def test_declaration_frozen(self):
        decl = OMVAdapter.capability_declaration()
        with self.assertRaises(AttributeError):
            decl.adapter_type = "other"


# ============================================================================
# Registry Integration
# ============================================================================

class TestOMVRegistryIntegration(unittest.TestCase):
    """注册表集成测试"""

    def test_register_to_registry(self):
        registry = AdapterCapabilityRegistry()
        OMVAdapter.register_to_registry(registry)
        self.assertTrue(registry.supports("omv", DeviceCapability.SYSTEM_INFO))

    def test_supports_all_capabilities(self):
        registry = AdapterCapabilityRegistry()
        OMVAdapter.register_to_registry(registry)
        for cap in OMV_CAPABILITIES:
            self.assertTrue(registry.supports("omv", cap))

    def test_supports_backup_target(self):
        registry = AdapterCapabilityRegistry()
        OMVAdapter.register_to_registry(registry)
        self.assertTrue(registry.supports("omv", DeviceCapability.BACKUP_TARGET))

    def test_does_not_support_backup_source(self):
        registry = AdapterCapabilityRegistry()
        OMVAdapter.register_to_registry(registry)
        self.assertFalse(registry.supports("omv", DeviceCapability.BACKUP_SOURCE))

    def test_pve_and_omv_independent(self):
        from backup_manager.adapters.pve_adapter import PVEAdapter
        registry = AdapterCapabilityRegistry()
        PVEAdapter.register_to_registry(registry)
        OMVAdapter.register_to_registry(registry)
        self.assertTrue(registry.supports("pve", DeviceCapability.SYSTEM_INFO))
        self.assertTrue(registry.supports("omv", DeviceCapability.BACKUP_TARGET))
        self.assertFalse(registry.supports("pve", DeviceCapability.BACKUP_TARGET))


# ============================================================================
# Client Contract
# ============================================================================

class TestOMVClientContract(unittest.TestCase):
    """客户端契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVClient, ABC))

    def test_has_get_system_info(self):
        self.assertTrue(hasattr(OMVClient, "get_system_info"))

    def test_has_get_storage(self):
        self.assertTrue(hasattr(OMVClient, "get_storage"))

    def test_has_get_status(self):
        self.assertTrue(hasattr(OMVClient, "get_status"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OMVClient()

    def test_concrete_subclass(self):
        class MockOMVClient(OMVClient):
            def get_system_info(self):
                return {"hostname": "omv1", "version": "6.0"}
            def get_storage(self):
                return [{"device": "/dev/sda", "mount_point": "/srv"}]
            def get_status(self):
                return {"status": "running", "cpu": 0.3}
        client = MockOMVClient()
        self.assertEqual(client.get_system_info()["hostname"], "omv1")

    def test_adapter_with_client(self):
        class MockOMVClient(OMVClient):
            def get_system_info(self):
                return OMVSystemInfo(
                    hostname="omv1", version="6.0", kernel="5.15",
                    uptime=3600, cpu_model="Intel", cpu_cores=4,
                    memory_total=8*1024**3, memory_used=4*1024**3,
                )
            def get_storage(self):
                return [OMVStorageInfo(
                    device="/dev/sda", mount_point="/srv", filesystem="ext4",
                    total=100*1024**3, used=50*1024**3, available=50*1024**3,
                )]
            def get_status(self):
                return {"status": "running"}
        adapter = OMVAdapter(client=MockOMVClient())
        adapter.connect({})
        info = adapter.query("system_info")
        self.assertEqual(info.hostname, "omv1")


# ============================================================================
# Query Tests
# ============================================================================

class TestOMVQuery(unittest.TestCase):
    """查询测试"""

    def setUp(self):
        self.adapter = OMVAdapter()
        self.adapter.connect({})

    def test_query_system_info(self):
        result = self.adapter.query("system_info")
        self.assertIsInstance(result, dict)

    def test_query_storage(self):
        result = self.adapter.query("storage")
        self.assertIsInstance(result, list)

    def test_query_status(self):
        result = self.adapter.query("status")
        self.assertIsInstance(result, dict)

    def test_query_unsupported(self):
        with self.assertRaises(OMVUnsupportedOperationError):
            self.adapter.query("backup")

    def test_query_not_connected(self):
        adapter = OMVAdapter()
        with self.assertRaises(AdapterNotConnectedError):
            adapter.query("system_info")

    def test_query_status_not_connected(self):
        adapter = OMVAdapter()
        with self.assertRaises(AdapterNotConnectedError):
            adapter.query_status()


# ============================================================================
# Readonly Boundary
# ============================================================================

class TestOMVReadonlyBoundary(unittest.TestCase):
    """只读边界测试"""

    def test_execute_rejected(self):
        adapter = OMVAdapter()
        with self.assertRaises(OMVUnsupportedOperationError):
            adapter.execute("ls")

    def test_modify_filesystem_not_exists(self):
        adapter = OMVAdapter()
        self.assertFalse(hasattr(adapter, "modify_filesystem"))

    def test_configure_smb_not_exists(self):
        adapter = OMVAdapter()
        self.assertFalse(hasattr(adapter, "configure_smb"))

    def test_configure_nfs_not_exists(self):
        adapter = OMVAdapter()
        self.assertFalse(hasattr(adapter, "configure_nfs"))

    def test_modify_raid_not_exists(self):
        adapter = OMVAdapter()
        self.assertFalse(hasattr(adapter, "modify_raid"))

    def test_create_user_not_exists(self):
        adapter = OMVAdapter()
        self.assertFalse(hasattr(adapter, "create_user"))

    def test_delete_user_not_exists(self):
        adapter = OMVAdapter()
        self.assertFalse(hasattr(adapter, "delete_user"))


# ============================================================================
# Result Models
# ============================================================================

class TestOMVResultModels(unittest.TestCase):
    """结果模型测试"""

    def test_system_info_frozen(self):
        info = OMVSystemInfo(
            hostname="omv1", version="6.0", kernel="5.15",
            uptime=3600, cpu_model="Intel", cpu_cores=4,
            memory_total=8*1024**3, memory_used=4*1024**3,
        )
        with self.assertRaises(AttributeError):
            info.hostname = "other"

    def test_storage_info_frozen(self):
        info = OMVStorageInfo(
            device="/dev/sda", mount_point="/srv", filesystem="ext4",
            total=100*1024**3, used=50*1024**3, available=50*1024**3,
        )
        with self.assertRaises(AttributeError):
            info.device = "other"

    def test_status_frozen(self):
        status = OMVStatus(
            hostname="omv1", status="running", cpu_usage=0.3,
            memory_usage=0.5, uptime=3600,
        )
        with self.assertRaises(AttributeError):
            status.hostname = "other"

    def test_system_info_no_credentials(self):
        info = OMVSystemInfo(
            hostname="omv1", version="6.0", kernel="5.15",
            uptime=3600, cpu_model="Intel", cpu_cores=4,
            memory_total=8*1024**3, memory_used=4*1024**3,
        )
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(info, attr))

    def test_storage_info_no_credentials(self):
        info = OMVStorageInfo(
            device="/dev/sda", mount_point="/srv", filesystem="ext4",
            total=100*1024**3, used=50*1024**3, available=50*1024**3,
        )
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(info, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestOMVErrorModel(unittest.TestCase):
    """错误模型测试"""

    def test_omv_adapter_error(self):
        with self.assertRaises(OMVAdapterError):
            raise OMVAdapterError("test")

    def test_omv_query_error(self):
        with self.assertRaises(OMVAdapterError):
            raise OMVQueryError("query failed")

    def test_unsupported_operation(self):
        exc = OMVUnsupportedOperationError("execute")
        self.assertIn("execute", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (OMVAdapterError, ("test",)),
            (OMVQueryError, ("test",)),
            (OMVUnsupportedOperationError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestOMVSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_adapter_no_secret_fields(self):
        adapter = OMVAdapter()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(adapter, attr))

    def test_models_no_credentials(self):
        for cls, kwargs in [
            (OMVSystemInfo, {"hostname":"o","version":"v","kernel":"k","uptime":1,"cpu_model":"c","cpu_cores":1,"memory_total":1,"memory_used":1}),
            (OMVStorageInfo, {"device":"d","mount_point":"m","filesystem":"f","total":1,"used":1,"available":1}),
            (OMVStatus, {"hostname":"o","status":"s","cpu_usage":0.1,"memory_usage":0.1,"uptime":1}),
        ]:
            obj = cls(**kwargs)
            for attr in ["password", "secret", "token", "credential", "endpoint"]:
                self.assertFalse(hasattr(obj, attr), f"{cls.__name__} has {attr}")

    def test_no_subprocess(self):
        import ast
        import os
        omv_dir = os.path.join("backup_manager", "adapters", "omv")
        for filename in os.listdir(omv_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(omv_dir, filename)
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
        for filepath in [
            "backup_manager/adapters/omv_adapter.py",
            "backup_manager/adapters/omv/errors.py",
            "backup_manager/adapters/omv/models.py",
            "backup_manager/adapters/omv/client.py",
        ]:
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filepath}")


if __name__ == "__main__":
    unittest.main()
