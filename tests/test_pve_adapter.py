"""
WorkOps PVE Adapter Tests
Sprint027: PVE ReadOnly Adapter

覆盖：
- PVEAdapter initialization
- Capability declaration
- Registry integration
- Client contract
- Result models
- Readonly boundary
- Security checks
"""

import unittest

from backup_manager.adapters.pve_adapter import PVEAdapter, PVE_CAPABILITIES
from backup_manager.adapters.pve import (
    PVEAdapterError,
    PVEQueryError,
    PVEUnsupportedOperationError,
    PVENodeInfo,
    PVEStorageInfo,
    PVEStatus,
    PVEClient,
)
from backup_manager.adapters.capability import AdapterCapabilityDeclaration
from backup_manager.adapters.capability_registry import AdapterCapabilityRegistry
from backup_manager.adapters.errors import AdapterNotConnectedError
from backup_manager.devices.capability import DeviceCapability


# ============================================================================
# PVEAdapter Initialization
# ============================================================================

class TestPVEAdapterInit(unittest.TestCase):
    """适配器初始化测试"""

    def test_adapter_type(self):
        adapter = PVEAdapter()
        self.assertEqual(adapter.adapter_type, "pve")

    def test_not_connected_by_default(self):
        adapter = PVEAdapter()
        self.assertFalse(adapter._connected)

    def test_connect(self):
        adapter = PVEAdapter()
        result = adapter.connect({})
        self.assertTrue(result)
        self.assertTrue(adapter._connected)

    def test_disconnect(self):
        adapter = PVEAdapter()
        adapter.connect({})
        adapter.disconnect()
        self.assertFalse(adapter._connected)

    def test_no_forbidden_methods(self):
        adapter = PVEAdapter()
        for method in ["create_vm", "delete_vm", "update_vm", "execute_command"]:
            self.assertFalse(
                hasattr(adapter, method),
                f"PVEAdapter should not have {method}"
            )


# ============================================================================
# Capability Declaration
# ============================================================================

class TestPVECapabilityDeclaration(unittest.TestCase):
    """能力声明测试"""

    def test_capability_count(self):
        self.assertEqual(len(PVE_CAPABILITIES), 3)

    def test_system_info(self):
        self.assertIn(DeviceCapability.SYSTEM_INFO, PVE_CAPABILITIES)

    def test_status_query(self):
        self.assertIn(DeviceCapability.STATUS_QUERY, PVE_CAPABILITIES)

    def test_storage_query(self):
        self.assertIn(DeviceCapability.STORAGE_QUERY, PVE_CAPABILITIES)

    def test_no_backup_capabilities(self):
        self.assertNotIn(DeviceCapability.BACKUP_SOURCE, PVE_CAPABILITIES)
        self.assertNotIn(DeviceCapability.BACKUP_TARGET, PVE_CAPABILITIES)

    def test_declaration_method(self):
        decl = PVEAdapter.capability_declaration()
        self.assertIsInstance(decl, AdapterCapabilityDeclaration)
        self.assertEqual(decl.adapter_type, "pve")

    def test_declaration_frozen(self):
        decl = PVEAdapter.capability_declaration()
        with self.assertRaises(AttributeError):
            decl.adapter_type = "other"


# ============================================================================
# Registry Integration
# ============================================================================

class TestPVERegistryIntegration(unittest.TestCase):
    """注册表集成测试"""

    def test_register_to_registry(self):
        registry = AdapterCapabilityRegistry()
        PVEAdapter.register_to_registry(registry)
        self.assertTrue(registry.supports("pve", DeviceCapability.SYSTEM_INFO))

    def test_supports_all_capabilities(self):
        registry = AdapterCapabilityRegistry()
        PVEAdapter.register_to_registry(registry)
        for cap in PVE_CAPABILITIES:
            self.assertTrue(registry.supports("pve", cap))

    def test_does_not_support_backup(self):
        registry = AdapterCapabilityRegistry()
        PVEAdapter.register_to_registry(registry)
        self.assertFalse(registry.supports("pve", DeviceCapability.BACKUP_SOURCE))


# ============================================================================
# Client Contract
# ============================================================================

class TestPVEClientContract(unittest.TestCase):
    """客户端契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEClient, ABC))

    def test_has_get_nodes(self):
        self.assertTrue(hasattr(PVEClient, "get_nodes"))

    def test_has_get_storage(self):
        self.assertTrue(hasattr(PVEClient, "get_storage"))

    def test_has_get_status(self):
        self.assertTrue(hasattr(PVEClient, "get_status"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PVEClient()

    def test_concrete_subclass(self):
        class MockPVEClient(PVEClient):
            def get_nodes(self):
                return [{"node": "pve1", "status": "online"}]
            def get_storage(self, node):
                return [{"storage": "local", "type": "dir"}]
            def get_status(self, node):
                return {"status": "running", "cpu": 0.5}
        client = MockPVEClient()
        self.assertEqual(len(client.get_nodes()), 1)

    def test_adapter_with_client(self):
        class MockPVEClient(PVEClient):
            def get_nodes(self):
                return [PVENodeInfo(
                    node="pve1", status="online", cpu_cores=8,
                    memory_total=16*1024**3, memory_used=8*1024**3, uptime=3600,
                )]
            def get_storage(self, node):
                return [PVEStorageInfo(
                    storage="local", node="pve1", storage_type="dir",
                    total=100*1024**3, used=50*1024**3, active=True,
                )]
            def get_status(self, node):
                return {"status": "running"}
        adapter = PVEAdapter(client=MockPVEClient())
        adapter.connect({})
        nodes = adapter.query("nodes")
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].node, "pve1")


# ============================================================================
# Query Tests
# ============================================================================

class TestPVEQuery(unittest.TestCase):
    """查询测试"""

    def setUp(self):
        self.adapter = PVEAdapter()
        self.adapter.connect({})

    def test_query_nodes(self):
        result = self.adapter.query("nodes")
        self.assertIsInstance(result, list)

    def test_query_storage(self):
        result = self.adapter.query("storage")
        self.assertIsInstance(result, list)

    def test_query_status(self):
        result = self.adapter.query("status")
        self.assertIsInstance(result, dict)

    def test_query_unsupported(self):
        with self.assertRaises(PVEUnsupportedOperationError):
            self.adapter.query("backup")

    def test_query_not_connected(self):
        adapter = PVEAdapter()
        with self.assertRaises(AdapterNotConnectedError):
            adapter.query("nodes")

    def test_query_status_not_connected(self):
        adapter = PVEAdapter()
        with self.assertRaises(AdapterNotConnectedError):
            adapter.query_status()


# ============================================================================
# Readonly Boundary
# ============================================================================

class TestPVEReadonlyBoundary(unittest.TestCase):
    """只读边界测试"""

    def test_execute_rejected(self):
        adapter = PVEAdapter()
        with self.assertRaises(PVEUnsupportedOperationError):
            adapter.execute("ls")

    def test_create_vm_not_exists(self):
        adapter = PVEAdapter()
        self.assertFalse(hasattr(adapter, "create_vm"))

    def test_delete_vm_not_exists(self):
        adapter = PVEAdapter()
        self.assertFalse(hasattr(adapter, "delete_vm"))

    def test_update_vm_not_exists(self):
        adapter = PVEAdapter()
        self.assertFalse(hasattr(adapter, "update_vm"))

    def test_execute_command_not_exists(self):
        adapter = PVEAdapter()
        self.assertFalse(hasattr(adapter, "execute_command"))


# ============================================================================
# Result Models
# ============================================================================

class TestPVEResultModels(unittest.TestCase):
    """结果模型测试"""

    def test_node_info_frozen(self):
        info = PVENodeInfo(
            node="pve1", status="online", cpu_cores=8,
            memory_total=16*1024**3, memory_used=8*1024**3, uptime=3600,
        )
        with self.assertRaises(AttributeError):
            info.node = "other"

    def test_storage_info_frozen(self):
        info = PVEStorageInfo(
            storage="local", node="pve1", storage_type="dir",
            total=100*1024**3, used=50*1024**3, active=True,
        )
        with self.assertRaises(AttributeError):
            info.storage = "other"

    def test_status_frozen(self):
        status = PVEStatus(
            node="pve1", status="running", cpu_usage=0.5,
            memory_usage=0.75, uptime=3600,
        )
        with self.assertRaises(AttributeError):
            status.node = "other"

    def test_node_info_no_credentials(self):
        info = PVENodeInfo(
            node="pve1", status="online", cpu_cores=8,
            memory_total=16*1024**3, memory_used=8*1024**3, uptime=3600,
        )
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(info, attr))


# ============================================================================
# Error Model
# ============================================================================

class TestPVEErrorModel(unittest.TestCase):
    """错误模型测试"""

    def test_pve_adapter_error(self):
        with self.assertRaises(PVEAdapterError):
            raise PVEAdapterError("test")

    def test_pve_query_error(self):
        with self.assertRaises(PVEAdapterError):
            raise PVEQueryError("query failed")

    def test_unsupported_operation(self):
        exc = PVEUnsupportedOperationError("execute")
        self.assertIn("execute", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (PVEAdapterError, ("test",)),
            (PVEQueryError, ("test",)),
            (PVEUnsupportedOperationError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestPVESecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_adapter_no_secret_fields(self):
        adapter = PVEAdapter()
        for attr in ["password", "secret", "token", "credential"]:
            self.assertFalse(hasattr(adapter, attr))

    def test_models_no_credentials(self):
        for cls, kwargs in [
            (PVENodeInfo, {"node":"n","status":"s","cpu_cores":1,"memory_total":1,"memory_used":1,"uptime":1}),
            (PVEStorageInfo, {"storage":"s","node":"n","storage_type":"t","total":1,"used":1,"active":True}),
            (PVEStatus, {"node":"n","status":"s","cpu_usage":0.1,"memory_usage":0.1,"uptime":1}),
        ]:
            obj = cls(**kwargs)
            for attr in ["password", "secret", "token", "credential", "endpoint"]:
                self.assertFalse(hasattr(obj, attr), f"{cls.__name__} has {attr}")

    def test_no_subprocess(self):
        import ast
        import os
        pve_dir = os.path.join("backup_manager", "adapters", "pve")
        for filename in os.listdir(pve_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(pve_dir, filename)
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
            "backup_manager/adapters/pve_adapter.py",
            "backup_manager/adapters/pve/errors.py",
            "backup_manager/adapters/pve/models.py",
            "backup_manager/adapters/pve/client.py",
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
