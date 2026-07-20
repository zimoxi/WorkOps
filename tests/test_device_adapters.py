"""
WorkOps Device Adapter Tests
Sprint017: Device Adapter Foundation

覆盖：
- BaseAdapter 抽象接口
- MockAdapter connect/disconnect
- 未连接异常
- Mock execute
- Mock query_status
- 三个占位 Adapter
- AdapterFactory
- 未知 Adapter 类型
- 禁止真实连接库检查
"""

import unittest
import os
import ast

from backup_manager.adapters.base import BaseAdapter
from backup_manager.adapters.mock_adapter import MockAdapter
from backup_manager.adapters.ssh_adapter import SSHAdapter
from backup_manager.adapters.winrm_adapter import WinRMAdapter
from backup_manager.adapters.snmp_adapter import SNMPAdapter
from backup_manager.adapters.factory import AdapterFactory
from backup_manager.adapters.errors import (
    AdapterError,
    AdapterNotConnectedError,
    AdapterNotImplementedError,
    AdapterExecutionError,
)


class TestBaseAdapterInterface(unittest.TestCase):
    """测试 BaseAdapter 抽象接口"""

    def test_base_adapter_has_connect(self):
        """验证 BaseAdapter 有 connect 方法"""
        self.assertTrue(hasattr(BaseAdapter, 'connect'))

    def test_base_adapter_has_disconnect(self):
        """验证 BaseAdapter 有 disconnect 方法"""
        self.assertTrue(hasattr(BaseAdapter, 'disconnect'))

    def test_base_adapter_has_execute(self):
        """验证 BaseAdapter 有 execute 方法"""
        self.assertTrue(hasattr(BaseAdapter, 'execute'))

    def test_base_adapter_has_query_status(self):
        """验证 BaseAdapter 有 query_status 方法"""
        self.assertTrue(hasattr(BaseAdapter, 'query_status'))

    def test_base_adapter_is_abstract(self):
        """验证 BaseAdapter 是抽象类"""
        with self.assertRaises(TypeError):
            BaseAdapter()


class TestMockAdapterConnectDisconnect(unittest.TestCase):
    """测试 MockAdapter connect/disconnect"""

    def test_mock_adapter_connect(self):
        """验证 MockAdapter 连接"""
        adapter = MockAdapter()
        result = adapter.connect({"id": "dev-001", "name": "Test"})
        self.assertTrue(result)
        self.assertTrue(adapter.connected)
        self.assertEqual(adapter.device["id"], "dev-001")

    def test_mock_adapter_disconnect(self):
        """验证 MockAdapter 断开"""
        adapter = MockAdapter()
        adapter.connect({"id": "dev-001"})
        adapter.disconnect()
        self.assertFalse(adapter.connected)
        self.assertIsNone(adapter.device)

    def test_mock_adapter_is_base_adapter(self):
        """验证 MockAdapter 继承 BaseAdapter"""
        adapter = MockAdapter()
        self.assertIsInstance(adapter, BaseAdapter)


class TestMockAdapterNotConnectedError(unittest.TestCase):
    """测试 MockAdapter 未连接异常"""

    def test_execute_raises_when_not_connected(self):
        """验证未连接时 execute 抛出异常"""
        adapter = MockAdapter()
        with self.assertRaises(AdapterNotConnectedError):
            adapter.execute("ls")

    def test_query_status_raises_when_not_connected(self):
        """验证未连接时 query_status 抛出异常"""
        adapter = MockAdapter()
        with self.assertRaises(AdapterNotConnectedError):
            adapter.query_status()


class TestMockAdapterExecute(unittest.TestCase):
    """测试 MockAdapter execute"""

    def test_mock_adapter_execute(self):
        """验证 MockAdapter 执行"""
        adapter = MockAdapter()
        adapter.connect({"id": "dev-001"})
        result = adapter.execute("ls -la")
        self.assertTrue(result["success"])
        self.assertIn("MOCK", result["stdout"])
        self.assertEqual(result["exit_code"], 0)

    def test_mock_adapter_execute_returns_dict(self):
        """验证 MockAdapter 返回字典"""
        adapter = MockAdapter()
        adapter.connect({"id": "dev-001"})
        result = adapter.execute("test")
        self.assertIsInstance(result, dict)
        self.assertIn("success", result)
        self.assertIn("stdout", result)
        self.assertIn("stderr", result)
        self.assertIn("exit_code", result)


class TestMockAdapterQueryStatus(unittest.TestCase):
    """测试 MockAdapter query_status"""

    def test_mock_adapter_query_status(self):
        """验证 MockAdapter 状态查询"""
        adapter = MockAdapter()
        adapter.connect({"id": "dev-001"})
        status = adapter.query_status()
        self.assertTrue(status["online"])
        self.assertIn("cpu_usage", status)
        self.assertIn("memory_usage", status)
        self.assertIn("disk_usage", status)

    def test_mock_adapter_query_status_returns_dict(self):
        """验证 MockAdapter 返回字典"""
        adapter = MockAdapter()
        adapter.connect({"id": "dev-001"})
        status = adapter.query_status()
        self.assertIsInstance(status, dict)


class TestPlaceholderAdapters(unittest.TestCase):
    """测试三个占位 Adapter"""

    def test_ssh_adapter_not_implemented(self):
        """验证 SSHAdapter 抛出未实现异常"""
        adapter = SSHAdapter()
        with self.assertRaises(AdapterNotImplementedError):
            adapter.connect({})
        with self.assertRaises(AdapterNotImplementedError):
            adapter.disconnect()
        with self.assertRaises(AdapterNotImplementedError):
            adapter.execute("test")
        with self.assertRaises(AdapterNotImplementedError):
            adapter.query_status()

    def test_winrm_adapter_not_implemented(self):
        """验证 WinRMAdapter 抛出未实现异常"""
        adapter = WinRMAdapter()
        with self.assertRaises(AdapterNotImplementedError):
            adapter.connect({})
        with self.assertRaises(AdapterNotImplementedError):
            adapter.disconnect()
        with self.assertRaises(AdapterNotImplementedError):
            adapter.execute("test")
        with self.assertRaises(AdapterNotImplementedError):
            adapter.query_status()

    def test_snmp_adapter_not_implemented(self):
        """验证 SNMPAdapter 抛出未实现异常"""
        adapter = SNMPAdapter()
        with self.assertRaises(AdapterNotImplementedError):
            adapter.connect({})
        with self.assertRaises(AdapterNotImplementedError):
            adapter.disconnect()
        with self.assertRaises(AdapterNotImplementedError):
            adapter.execute("test")
        with self.assertRaises(AdapterNotImplementedError):
            adapter.query_status()

    def test_ssh_adapter_is_base_adapter(self):
        """验证 SSHAdapter 继承 BaseAdapter"""
        adapter = SSHAdapter()
        self.assertIsInstance(adapter, BaseAdapter)

    def test_winrm_adapter_is_base_adapter(self):
        """验证 WinRMAdapter 继承 BaseAdapter"""
        adapter = WinRMAdapter()
        self.assertIsInstance(adapter, BaseAdapter)

    def test_snmp_adapter_is_base_adapter(self):
        """验证 SNMPAdapter 继承 BaseAdapter"""
        adapter = SNMPAdapter()
        self.assertIsInstance(adapter, BaseAdapter)


class TestAdapterFactory(unittest.TestCase):
    """测试 AdapterFactory"""

    def test_factory_create_mock(self):
        """验证 AdapterFactory 创建 MockAdapter"""
        adapter = AdapterFactory.create("mock")
        self.assertIsInstance(adapter, MockAdapter)

    def test_factory_create_ssh(self):
        """验证 AdapterFactory 创建 SSHAdapter"""
        adapter = AdapterFactory.create("ssh")
        self.assertIsInstance(adapter, SSHAdapter)

    def test_factory_create_winrm(self):
        """验证 AdapterFactory 创建 WinRMAdapter"""
        adapter = AdapterFactory.create("winrm")
        self.assertIsInstance(adapter, WinRMAdapter)

    def test_factory_create_snmp(self):
        """验证 AdapterFactory 创建 SNMPAdapter"""
        adapter = AdapterFactory.create("snmp")
        self.assertIsInstance(adapter, SNMPAdapter)

    def test_factory_create_unknown(self):
        """验证 AdapterFactory 未知类型抛出异常"""
        with self.assertRaises(AdapterNotImplementedError):
            AdapterFactory.create("unknown")

    def test_factory_create_returns_base_adapter(self):
        """验证 AdapterFactory 返回 BaseAdapter"""
        adapter = AdapterFactory.create("mock")
        self.assertIsInstance(adapter, BaseAdapter)


class TestNoRealConnectionLibraries(unittest.TestCase):
    """测试禁止真实连接库"""

    def test_no_paramiko_import(self):
        """验证占位 Adapter 未导入 paramiko"""
        # Sprint022 ssh_paramiko_client.py 和 ssh_readonly_adapter.py
        # 合法使用 paramiko，不在此检查范围
        excluded = {'ssh_paramiko_client.py', 'ssh_readonly_adapter.py'}
        adapters_dir = os.path.join(os.path.dirname(__file__), '..', 'backup_manager', 'adapters')
        for filename in os.listdir(adapters_dir):
            if filename.endswith('.py') and filename not in excluded:
                filepath = os.path.join(adapters_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                # 使用 AST 扫描 import 语句
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self.assertNotEqual(alias.name, 'paramiko',
                                    f"paramiko imported in {filename}")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and 'paramiko' in node.module:
                                self.fail(f"paramiko imported in {filename}")
                except SyntaxError:
                    pass

    def test_no_pywinrm_import(self):
        """验证未导入 pywinrm"""
        adapters_dir = os.path.join(os.path.dirname(__file__), '..', 'backup_manager', 'adapters')
        for filename in os.listdir(adapters_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(adapters_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                # 只检查实际库导入，不检查类名
                                if alias.name in ['pywinrm']:
                                    self.fail(f"pywinrm imported in {filename}")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and node.module in ['pywinrm']:
                                self.fail(f"pywinrm imported in {filename}")
                except SyntaxError:
                    pass

    def test_no_pysnmp_import(self):
        """验证未导入 pysnmp"""
        adapters_dir = os.path.join(os.path.dirname(__file__), '..', 'backup_manager', 'adapters')
        for filename in os.listdir(adapters_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(adapters_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self.assertNotEqual(alias.name, 'pysnmp',
                                    f"pysnmp imported in {filename}")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and 'pysnmp' in node.module:
                                self.fail(f"pysnmp imported in {filename}")
                except SyntaxError:
                    pass


if __name__ == '__main__':
    unittest.main()
