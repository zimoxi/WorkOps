"""
WorkOps Adapter Runtime Tests
Sprint023: Adapter Runtime Integration Foundation

覆盖：
- AdapterCapability enum
- AdapterDescriptor validation
- AdapterRegistry register/create/reject
- AdapterSession state machine
- AdapterRuntime lifecycle
- Security boundary checks
"""

import unittest
from datetime import datetime, timezone

from backup_manager.adapters.capabilities import AdapterCapability
from backup_manager.adapters.descriptor import AdapterDescriptor
from backup_manager.adapters.registry import AdapterRegistry
from backup_manager.adapters.session import AdapterSession, SessionState
from backup_manager.adapters.runtime import AdapterRuntime
from backup_manager.adapters.result import AdapterQueryResult
from backup_manager.adapters.mock_adapter import MockAdapter
from backup_manager.adapters.errors import (
    AdapterDescriptorError,
    AdapterDuplicateError,
    AdapterNotRegisteredError,
    AdapterSessionStateError,
    AdapterError,
)


# ============================================================================
# AdapterCapability
# ============================================================================

class TestAdapterCapability(unittest.TestCase):
    """能力枚举测试"""

    def test_status_query_exists(self):
        self.assertEqual(AdapterCapability.STATUS_QUERY.value, "status_query")

    def test_system_query_exists(self):
        self.assertEqual(AdapterCapability.SYSTEM_QUERY.value, "system_query")

    def test_no_execute_capability(self):
        values = {c.value for c in AdapterCapability}
        self.assertNotIn("execute", values)
        self.assertNotIn("upload", values)
        self.assertNotIn("download", values)
        self.assertNotIn("backup", values)
        self.assertNotIn("restore", values)

    def test_frozen_enum(self):
        self.assertIsInstance(AdapterCapability.STATUS_QUERY, AdapterCapability)
        self.assertEqual(len(AdapterCapability), 2)

    def test_enum_comparison(self):
        self.assertIsNot(AdapterCapability.STATUS_QUERY, AdapterCapability.SYSTEM_QUERY)
        self.assertEqual(AdapterCapability("status_query"), AdapterCapability.STATUS_QUERY)


# ============================================================================
# AdapterDescriptor
# ============================================================================

class TestAdapterDescriptor(unittest.TestCase):
    """描述符测试"""

    def test_valid_descriptor(self):
        desc = AdapterDescriptor(
            adapter_type="test",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        self.assertEqual(desc.adapter_type, "test")
        self.assertIn(AdapterCapability.STATUS_QUERY, desc.capabilities)
        self.assertTrue(desc.readonly)

    def test_frozen(self):
        desc = AdapterDescriptor(
            adapter_type="test",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        with self.assertRaises(AttributeError):
            desc.adapter_type = "other"

    def test_empty_adapter_type_rejected(self):
        with self.assertRaises(AdapterDescriptorError):
            AdapterDescriptor(
                adapter_type="",
                capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
                readonly=True,
            )

    def test_whitespace_adapter_type_rejected(self):
        with self.assertRaises(AdapterDescriptorError):
            AdapterDescriptor(
                adapter_type="   ",
                capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
                readonly=True,
            )

    def test_empty_capabilities_rejected(self):
        with self.assertRaises(AdapterDescriptorError):
            AdapterDescriptor(
                adapter_type="test",
                capabilities=frozenset(),
                readonly=True,
            )

    def test_readonly_must_be_true(self):
        with self.assertRaises(AdapterDescriptorError):
            AdapterDescriptor(
                adapter_type="test",
                capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
                readonly=False,
            )

    def test_invalid_capability_rejected(self):
        with self.assertRaises(AdapterDescriptorError):
            AdapterDescriptor(
                adapter_type="test",
                capabilities=frozenset({"not_a_capability"}),
                readonly=True,
            )

    def test_two_capabilities(self):
        desc = AdapterDescriptor(
            adapter_type="ssh_readonly",
            capabilities=frozenset({
                AdapterCapability.STATUS_QUERY,
                AdapterCapability.SYSTEM_QUERY,
            }),
            readonly=True,
        )
        self.assertEqual(len(desc.capabilities), 2)


# ============================================================================
# AdapterRegistry
# ============================================================================

class TestAdapterRegistry(unittest.TestCase):
    """注册表测试"""

    def setUp(self):
        self.registry = AdapterRegistry()
        self.desc = AdapterDescriptor(
            adapter_type="mock",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )

    def test_register_and_get(self):
        self.registry.register(self.desc, MockAdapter)
        got = self.registry.get_descriptor("mock")
        self.assertEqual(got.adapter_type, "mock")

    def test_duplicate_rejected(self):
        self.registry.register(self.desc, MockAdapter)
        with self.assertRaises(AdapterDuplicateError):
            self.registry.register(self.desc, MockAdapter)

    def test_unknown_type_rejected(self):
        with self.assertRaises(AdapterNotRegisteredError):
            self.registry.get_descriptor("nonexistent")

    def test_create_adapter(self):
        self.registry.register(self.desc, MockAdapter)
        adapter = self.registry.create("mock")
        self.assertIsInstance(adapter, MockAdapter)

    def test_create_unknown_rejected(self):
        with self.assertRaises(AdapterNotRegisteredError):
            self.registry.create("nonexistent")

    def test_list_types(self):
        self.registry.register(self.desc, MockAdapter)
        types = self.registry.list_types()
        self.assertIn("mock", types)

    def test_is_registered(self):
        self.assertFalse(self.registry.is_registered("mock"))
        self.registry.register(self.desc, MockAdapter)
        self.assertTrue(self.registry.is_registered("mock"))

    def test_register_non_descriptor_rejected(self):
        with self.assertRaises(TypeError):
            self.registry.register("not_a_descriptor", MockAdapter)


# ============================================================================
# AdapterSession
# ============================================================================

class TestAdapterSession(unittest.TestCase):
    """会话状态机测试"""

    def test_create_session(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        self.assertEqual(session.state, SessionState.CREATED)
        self.assertIsNotNone(session.session_id)
        self.assertEqual(session.adapter_type, "mock")
        self.assertEqual(session.device_id, "dev-1")

    def test_transition_to_connected(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        session.transition(SessionState.CONNECTED)
        self.assertEqual(session.state, SessionState.CONNECTED)
        self.assertIsNotNone(session.connected_at)

    def test_transition_to_closed(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        session.transition(SessionState.CONNECTED)
        session.transition(SessionState.CLOSED)
        self.assertEqual(session.state, SessionState.CLOSED)
        self.assertTrue(session.is_closed)
        self.assertIsNotNone(session.closed_at)

    def test_direct_close_from_created(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        session.transition(SessionState.CLOSED)
        self.assertTrue(session.is_closed)

    def test_invalid_transition_rejected(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        session.transition(SessionState.CONNECTED)
        with self.assertRaises(AdapterSessionStateError):
            session.transition(SessionState.CREATED)

    def test_cannot_connect_after_closed(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        session.transition(SessionState.CLOSED)
        with self.assertRaises(AdapterSessionStateError):
            session.transition(SessionState.CONNECTED)

    def test_close_idempotent(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        session.transition(SessionState.CLOSED)
        # 已关闭不能再转换
        with self.assertRaises(AdapterSessionStateError):
            session.transition(SessionState.CLOSED)

    def test_timestamps(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        self.assertIsNotNone(session.created_at)
        self.assertIsNone(session.connected_at)
        self.assertIsNone(session.closed_at)

    def test_device_id_preserved(self):
        session = AdapterSession(adapter_type="ssh_readonly", device_id="192.168.1.1")
        self.assertEqual(session.device_id, "192.168.1.1")
        session.transition(SessionState.CONNECTED)
        self.assertEqual(session.device_id, "192.168.1.1")

    def test_adapter_type_preserved(self):
        session = AdapterSession(adapter_type="ssh_readonly", device_id="dev-1")
        self.assertEqual(session.adapter_type, "ssh_readonly")
        session.transition(SessionState.CLOSED)
        self.assertEqual(session.adapter_type, "ssh_readonly")


# ============================================================================
# AdapterRuntime
# ============================================================================

class TestAdapterRuntime(unittest.TestCase):
    """Runtime 生命周期测试"""

    def setUp(self):
        self.registry = AdapterRegistry()
        desc = AdapterDescriptor(
            adapter_type="mock",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        self.registry.register(desc, MockAdapter)
        self.runtime = AdapterRuntime(self.registry)

    def test_create_session(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.assertEqual(session.state, SessionState.CREATED)
        self.assertEqual(session.adapter_type, "mock")

    def test_create_session_unknown_type(self):
        with self.assertRaises(AdapterNotRegisteredError):
            self.runtime.create_session("nonexistent", "dev-1")

    def test_connect(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.connect(session.session_id)
        updated = self.runtime.get_session(session.session_id)
        self.assertEqual(updated.state, SessionState.CONNECTED)

    def test_connect_passes_kwargs_to_registry(self):
        """Mock adapter 不需要 kwargs，但 ssh_readonly 需要。验证 kwargs 传递。"""
        session = self.runtime.create_session("mock", "dev-1")
        # Mock 不需要 kwargs
        self.runtime.connect(session.session_id)

    def test_query(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.connect(session.session_id)
        result = self.runtime.query(session.session_id, "system.hostname")
        self.assertIsInstance(result, AdapterQueryResult)
        self.assertTrue(result.success)
        self.assertEqual(result.query_id, "system.hostname")
        self.assertIn("stdout", result.data)

    def test_query_not_connected_rejected(self):
        session = self.runtime.create_session("mock", "dev-1")
        with self.assertRaises(AdapterSessionStateError):
            self.runtime.query(session.session_id, "system.hostname")

    def test_close(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.connect(session.session_id)
        self.runtime.close(session.session_id)
        updated = self.runtime.get_session(session.session_id)
        self.assertEqual(updated.state, SessionState.CLOSED)

    def test_close_idempotent(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.connect(session.session_id)
        self.runtime.close(session.session_id)
        # 再次关闭不报错
        self.runtime.close(session.session_id)

    def test_close_from_created(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.close(session.session_id)
        updated = self.runtime.get_session(session.session_id)
        self.assertEqual(updated.state, SessionState.CLOSED)

    def test_query_after_close_rejected(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.connect(session.session_id)
        self.runtime.close(session.session_id)
        with self.assertRaises(AdapterSessionStateError):
            self.runtime.query(session.session_id, "system.hostname")

    def test_unknown_session_rejected(self):
        with self.assertRaises(AdapterSessionStateError):
            self.runtime.get_session("nonexistent")

    def test_full_lifecycle(self):
        session = self.runtime.create_session("mock", "dev-1")
        self.runtime.connect(session.session_id)
        result = self.runtime.query(session.session_id, "system.hostname")
        self.assertTrue(result.success)
        self.runtime.close(session.session_id)
        updated = self.runtime.get_session(session.session_id)
        self.assertTrue(updated.is_closed)


# ============================================================================
# AdapterQueryResult
# ============================================================================

class TestAdapterQueryResult(unittest.TestCase):
    """统一查询结果测试"""

    def test_frozen(self):
        result = AdapterQueryResult(
            query_id="test",
            success=True,
            data={"key": "value"},
            message="ok",
            timestamp="2026-01-01T00:00:00",
        )
        with self.assertRaises(AttributeError):
            result.query_id = "other"

    def test_fields(self):
        result = AdapterQueryResult(
            query_id="system.hostname",
            success=True,
            data={"stdout": "host1"},
            message="",
            timestamp="2026-01-01T00:00:00",
        )
        self.assertEqual(result.query_id, "system.hostname")
        self.assertTrue(result.success)
        self.assertEqual(result.data["stdout"], "host1")

    def test_no_command_field(self):
        """确认结果中没有 command 字段"""
        result = AdapterQueryResult(
            query_id="test",
            success=True,
            data={},
            message="",
            timestamp="",
        )
        self.assertFalse(hasattr(result, "command"))
        self.assertFalse(hasattr(result, "stdout"))
        self.assertFalse(hasattr(result, "stderr"))
        self.assertFalse(hasattr(result, "password"))
        self.assertFalse(hasattr(result, "secret_ref"))


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_session_no_secret_fields(self):
        session = AdapterSession(adapter_type="mock", device_id="dev-1")
        # Session 不应有 secret/password/credential 属性
        for attr in ["password", "secret", "secret_ref", "credential", "token", "private_key"]:
            self.assertFalse(
                hasattr(session, attr),
                f"Session should not have {attr}"
            )

    def test_result_no_secret_fields(self):
        result = AdapterQueryResult(
            query_id="test",
            success=True,
            data={},
            message="",
            timestamp="",
        )
        for attr in ["password", "secret", "secret_ref", "credential", "token",
                      "private_key", "command"]:
            self.assertFalse(
                hasattr(result, attr),
                f"Result should not have {attr}"
            )

    def test_runtime_no_secret_storage(self):
        registry = AdapterRegistry()
        desc = AdapterDescriptor(
            adapter_type="mock",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        registry.register(desc, MockAdapter)
        runtime = AdapterRuntime(registry)
        session = runtime.create_session("mock", "dev-1")
        runtime.connect(session.session_id)
        # Runtime 内部不应保存任何 secret
        for attr in ["password", "secret", "secret_ref", "credential", "token"]:
            self.assertFalse(
                hasattr(runtime, attr),
                f"Runtime should not have {attr}"
            )

    def test_error_messages_no_secrets(self):
        """错误消息不泄漏 secret"""
        try:
            raise AdapterSessionStateError("test error")
        except AdapterSessionStateError as e:
            msg = str(e)
            self.assertNotIn("password", msg.lower())
            self.assertNotIn("secret", msg.lower())

    def test_descriptor_repr_no_secrets(self):
        desc = AdapterDescriptor(
            adapter_type="test",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        r = repr(desc)
        self.assertNotIn("password", r.lower())
        self.assertNotIn("secret", r.lower())

    def test_no_dynamic_import(self):
        """确认 registry 不使用动态 import"""
        import ast
        with open("backup_manager/adapters/registry.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name) and func.id in ("__import__", "import_module"):
                    self.fail("registry uses dynamic import")

    def test_runtime_repr_no_secrets(self):
        """Runtime repr 不泄漏 secret"""
        registry = AdapterRegistry()
        desc = AdapterDescriptor(
            adapter_type="mock",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        registry.register(desc, MockAdapter)
        runtime = AdapterRuntime(registry)
        r = repr(runtime)
        self.assertNotIn("password", r.lower())
        self.assertNotIn("secret", r.lower())
        self.assertNotIn("token", r.lower())


# ============================================================================
# Factory Registration
# ============================================================================

class TestFactoryRegistration(unittest.TestCase):
    """Factory 注册集成测试"""

    def test_register_to_registry(self):
        from backup_manager.adapters.factory import AdapterFactory
        registry = AdapterRegistry()
        AdapterFactory.register_to_registry(registry)
        self.assertTrue(registry.is_registered("mock"))
        self.assertTrue(registry.is_registered("ssh_readonly"))

    def test_mock_descriptor(self):
        from backup_manager.adapters.factory import AdapterFactory
        registry = AdapterRegistry()
        AdapterFactory.register_to_registry(registry)
        desc = registry.get_descriptor("mock")
        self.assertEqual(desc.adapter_type, "mock")
        self.assertTrue(desc.readonly)
        self.assertIn(AdapterCapability.STATUS_QUERY, desc.capabilities)

    def test_ssh_readonly_descriptor(self):
        from backup_manager.adapters.factory import AdapterFactory
        registry = AdapterRegistry()
        AdapterFactory.register_to_registry(registry)
        desc = registry.get_descriptor("ssh_readonly")
        self.assertEqual(desc.adapter_type, "ssh_readonly")
        self.assertTrue(desc.readonly)
        self.assertIn(AdapterCapability.STATUS_QUERY, desc.capabilities)
        self.assertIn(AdapterCapability.SYSTEM_QUERY, desc.capabilities)


if __name__ == "__main__":
    unittest.main()
