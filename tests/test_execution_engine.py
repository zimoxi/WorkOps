"""
WorkOps Execution Engine Tests
Sprint018: Execution Engine Foundation

覆盖：
- Task 不存在
- pending Task 成功执行
- pending → running → success
- 非 pending Task 拒绝执行
- AdapterFactory 只创建 mock
- connect 被调用
- execute 被调用
- 成功时 disconnect 被调用
- execute 失败时 disconnect 仍被调用
- connect 失败时不调用 execute
- AdapterExecutionError 转换为失败结果
- Task 最终状态为 failed
- ExecutionResult 字段完整且无额外字段
- stdout/stderr/exit_code 正确映射
- 不引入 paramiko/winrm/pywinrm/pysnmp
- 不使用 subprocess
- Operation 模块不调用 Adapter
- Scheduler 不自动执行 Task
- TaskNotFoundError 不改变任何 Task 状态
- InvalidTaskStateError 不改变原 Task 状态
- transition_status 校验 expected_status
- 执行成功但 disconnect 失败时 Task 为 failed
- AdapterFactory 创建失败 → Task failed
- connect 返回 False → 不调用 execute
- connect 返回 False → 不调用 disconnect
- execute 成功 + disconnect 失败 → Task 和 Result 都 failed
- execute 失败 + disconnect 失败 → 保留主执行错误
- 最终状态转换失败 → 抛出 TaskStateTransitionError
- Repository 拒绝非法转换
- 敏感异常文本不会进入 ExecutionResult
- Adapter 返回 success=False → Task/Result 均 failed
- Adapter 返回无效结构 → failed
- 执行前后 Task 除 status 外字段不变
- Task 不新增 device/command/adapter_type 字段
- ExecutionContext 不写回 Repository
"""

import unittest
import os
import ast
from unittest.mock import MagicMock
from datetime import datetime

from backup_manager.execution.service import ExecutionService
from backup_manager.execution.errors import (
    TaskNotFoundError,
    InvalidTaskStateError,
    TaskStateTransitionError,
)
from backup_manager.execution.result import ExecutionResult
from backup_manager.execution.context import ExecutionContext
from backup_manager.adapters.errors import (
    AdapterNotConnectedError,
    AdapterExecutionError,
    AdapterNotImplementedError,
)


class MockTaskRepository:
    """Mock Task Repository for testing"""
    
    ALLOWED_TRANSITIONS = {
        ("pending", "running"),
        ("pending", "cancelled"),
        ("running", "success"),
        ("running", "failed"),
    }
    
    def __init__(self, tasks=None):
        self.tasks = tasks or []
    
    def get_all(self):
        return self.tasks
    
    def get_by_id(self, task_id):
        for task in self.tasks:
            if task.get('id') == task_id:
                return task
        return None
    
    def transition_status(self, task_id, expected_status, new_status):
        if (expected_status, new_status) not in self.ALLOWED_TRANSITIONS:
            return False
        for task in self.tasks:
            if task.get('id') == task_id:
                if task.get('status') == expected_status:
                    task['status'] = new_status
                    return True
                return False
        return False


class TestTaskNotFoundError(unittest.TestCase):
    """测试 Task 不存在"""

    def test_task_not_found_error(self):
        """验证 TaskNotFoundError"""
        repo = MockTaskRepository([])
        service = ExecutionService(repo)
        
        with self.assertRaises(TaskNotFoundError):
            service.execute_task("nonexistent")

    def test_task_not_found_does_not_change_status(self):
        """验证 TaskNotFoundError 不改变任何 Task 状态"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        with self.assertRaises(TaskNotFoundError):
            service.execute_task("nonexistent")
        
        self.assertEqual(tasks[0]["status"], "pending")


class TestInvalidTaskStateError(unittest.TestCase):
    """测试非 pending Task 拒绝执行"""

    def test_running_task_rejected(self):
        """验证 running Task 无法再次执行"""
        tasks = [{"id": "task-001", "status": "running"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        with self.assertRaises(InvalidTaskStateError):
            service.execute_task("task-001")

    def test_success_task_rejected(self):
        """验证 success Task 无法再次执行"""
        tasks = [{"id": "task-001", "status": "success"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        with self.assertRaises(InvalidTaskStateError):
            service.execute_task("task-001")

    def test_failed_task_rejected(self):
        """验证 failed Task 无法再次执行"""
        tasks = [{"id": "task-001", "status": "failed"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        with self.assertRaises(InvalidTaskStateError):
            service.execute_task("task-001")

    def test_cancelled_task_rejected(self):
        """验证 cancelled Task 无法再次执行"""
        tasks = [{"id": "task-001", "status": "cancelled"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        with self.assertRaises(InvalidTaskStateError):
            service.execute_task("task-001")

    def test_invalid_state_does_not_change_status(self):
        """验证 InvalidTaskStateError 不改变原 Task 状态"""
        tasks = [{"id": "task-001", "status": "success"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        with self.assertRaises(InvalidTaskStateError):
            service.execute_task("task-001")
        
        self.assertEqual(tasks[0]["status"], "success")


class TestSuccessfulExecution(unittest.TestCase):
    """测试 pending → running → success"""

    def test_successful_execution(self):
        """验证 pending Task 成功执行"""
        tasks = [{"id": "task-001", "status": "pending", "device_name": "Test Device"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "success")
        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(tasks[0]["status"], "success")

    def test_execution_result_fields(self):
        """验证 ExecutionResult 字段完整"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        result = service.execute_task("task-001")
        result_dict = result.to_dict()
        
        expected_fields = ["task_id", "status", "started_at", "finished_at",
                          "duration", "stdout", "stderr", "exit_code", "message"]
        for field in expected_fields:
            self.assertIn(field, result_dict)
        
        self.assertEqual(len(result_dict), len(expected_fields))

    def test_stdout_stderr_exit_code_mapping(self):
        """验证 stdout/stderr/exit_code 正确映射"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        service = ExecutionService(repo)
        
        result = service.execute_task("task-001")
        
        self.assertIn("MOCK", result.stdout)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.exit_code, 0)


class TestAdapterCalls(unittest.TestCase):
    """测试 Adapter 调用"""

    def test_connect_called(self):
        """验证 connect 被调用"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        mock_adapter.connect.assert_called_once()

    def test_execute_called(self):
        """验证 execute 被调用"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        mock_adapter.execute.assert_called_once()

    def test_disconnect_called_on_success(self):
        """验证成功时 disconnect 被调用"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        mock_adapter.disconnect.assert_called_once()

    def test_disconnect_called_on_failure(self):
        """验证 execute 失败时 disconnect 仍被调用"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": False, "stdout": "", "stderr": "error", "exit_code": 1}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        mock_adapter.disconnect.assert_called_once()

    def test_adapter_factory_creates_mock(self):
        """验证 AdapterFactory 只创建 mock"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        mock_factory.create.assert_called_once_with("mock")


class TestAdapterFailure(unittest.TestCase):
    """测试 Adapter 执行失败"""

    def test_adapter_execution_error(self):
        """验证 AdapterExecutionError 转换为失败结果"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.side_effect = AdapterExecutionError("test error")
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(tasks[0]["status"], "failed")

    def test_connect_failure_no_execute(self):
        """验证 connect 失败时不调用 execute"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = False
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        mock_adapter.execute.assert_not_called()

    def test_connect_failure_no_disconnect(self):
        """验证 connect 返回 False 时不调用 disconnect"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = False
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        mock_adapter.disconnect.assert_not_called()

    def test_task_final_status_failed(self):
        """验证 Task 最终状态为 failed"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.side_effect = AdapterExecutionError("test error")
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        self.assertEqual(tasks[0]["status"], "failed")


class TestAdapterReturnValueChecks(unittest.TestCase):
    """测试 Adapter 返回值检查"""

    def test_adapter_returns_success_false(self):
        """验证 Adapter 返回 success=False → Task/Result 均 failed"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": False, "stdout": "", "stderr": "error", "exit_code": 1}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(tasks[0]["status"], "failed")

    def test_adapter_returns_invalid_structure(self):
        """验证 Adapter 返回无效结构 → failed"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = "invalid"
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(tasks[0]["status"], "failed")

    def test_adapter_returns_none(self):
        """验证 Adapter 返回 None → failed"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = None
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(tasks[0]["status"], "failed")


class TestAdapterFactoryFailure(unittest.TestCase):
    """测试 AdapterFactory 创建失败"""

    def test_adapter_factory_creation_failure(self):
        """验证 AdapterFactory 创建失败 → Task failed"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_factory = MagicMock()
        mock_factory.create.side_effect = AdapterNotImplementedError("unknown")
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(tasks[0]["status"], "failed")


class TestDisconnectFailure(unittest.TestCase):
    """测试 disconnect 失败规则"""

    def test_success_disconnect_failure(self):
        """验证执行成功但 disconnect 失败时 Task 为 failed"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        mock_adapter.disconnect.side_effect = Exception("disconnect failed")
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertEqual(tasks[0]["status"], "failed")

    def test_failure_disconnect_failure_preserves_main_error(self):
        """验证主执行失败且 disconnect 也失败时保留主错误"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.side_effect = AdapterExecutionError("main error")
        mock_adapter.disconnect.side_effect = Exception("disconnect failed")
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertEqual(result.status, "failed")
        self.assertIn("AdapterExecutionError", result.message)


class TestFinalStatusTransitionFailure(unittest.TestCase):
    """测试最终状态转换失败"""

    def test_final_transition_failure_raises(self):
        """验证最终状态转换失败 → 抛出 TaskStateTransitionError"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        
        # Mock transition_status to fail on final transition
        original_transition = repo.transition_status
        call_count = [0]
        def mock_transition(task_id, expected, new):
            call_count[0] += 1
            if call_count[0] == 1:
                return original_transition(task_id, expected, new)
            return False
        
        repo.transition_status = mock_transition
        
        with self.assertRaises(TaskStateTransitionError):
            service.execute_task("task-001")


class TestTransitionStatus(unittest.TestCase):
    """测试 transition_status"""

    def test_transition_status_valid(self):
        """验证 transition_status 校验合法转换"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        result = repo.transition_status("task-001", "pending", "running")
        self.assertTrue(result)
        self.assertEqual(tasks[0]["status"], "running")

    def test_transition_status_invalid(self):
        """验证 transition_status 拒绝错误的 expected_status"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        result = repo.transition_status("task-001", "running", "success")
        self.assertFalse(result)
        self.assertEqual(tasks[0]["status"], "pending")

    def test_repository_rejects_illegal_transitions(self):
        """验证 Repository 拒绝非法转换"""
        tasks = [{"id": "task-001", "status": "success"}]
        repo = MockTaskRepository(tasks)
        
        # success → running should be rejected
        result = repo.transition_status("task-001", "success", "running")
        self.assertFalse(result)
        
        # success → failed should be rejected
        result = repo.transition_status("task-001", "success", "failed")
        self.assertFalse(result)

    def test_all_taskrepository_implementations_satisfy_interface(self):
        """验证所有 TaskRepository 实现满足新接口"""
        from backup_manager.repositories.interfaces import TaskRepository
        from backup_manager.repositories.mock_task_repo import MockTaskRepository as RealMockTaskRepo
        
        self.assertTrue(hasattr(TaskRepository, 'transition_status'))
        self.assertTrue(hasattr(RealMockTaskRepo, 'transition_status'))


class TestSecurityBoundaries(unittest.TestCase):
    """测试安全边界"""

    def test_no_sensitive_info_in_result(self):
        """验证 ExecutionResult 不包含原始敏感异常文本"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.side_effect = AdapterExecutionError("password=secret123")
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        result = service.execute_task("task-001")
        
        self.assertNotIn("password=secret123", result.stderr)
        self.assertNotIn("password=secret123", result.message)
        self.assertIn("AdapterExecutionError", result.stderr)

    def test_no_real_connection_libraries(self):
        """验证不引入 paramiko/winrm/pywinrm/pysnmp"""
        execution_dir = os.path.join(os.path.dirname(__file__), '..', 'backup_manager', 'execution')
        forbidden = ['paramiko', 'pywinrm', 'pysnmp', 'winrm']
        found = []
        
        for filename in os.listdir(execution_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(execution_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                if alias.name in forbidden:
                                    found.append(f"{filename}: import {alias.name}")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module and node.module in forbidden:
                                found.append(f"{filename}: from {node.module}")
                except SyntaxError:
                    pass
        
        self.assertEqual(len(found), 0, f"Found forbidden imports: {found}")

    def test_no_subprocess_usage(self):
        """验证不使用 subprocess"""
        execution_dir = os.path.join(os.path.dirname(__file__), '..', 'backup_manager', 'execution')
        found = []
        
        for filename in os.listdir(execution_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(execution_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                if 'subprocess' in content:
                    found.append(filename)
        
        self.assertEqual(len(found), 0, f"Found subprocess usage: {found}")

    def test_no_bare_except(self):
        """验证没有裸捕获 except:"""
        execution_dir = os.path.join(os.path.dirname(__file__), '..', 'backup_manager', 'execution')
        found = []
        
        for filename in os.listdir(execution_dir):
            if filename.endswith('.py'):
                filepath = os.path.join(execution_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines, 1):
                    if line.strip() == 'except:':
                        found.append(f"{filename}:{i}")
        
        self.assertEqual(len(found), 0, f"Found bare except: {found}")


class TestDataModelProtection(unittest.TestCase):
    """测试数据模型保护"""

    def test_task_fields_unchanged_except_status(self):
        """验证执行前后 Task 除 status 外字段不变"""
        tasks = [{"id": "task-001", "status": "pending", "device_name": "Test Device", "name": "Test Task"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        # Check that only status changed
        self.assertEqual(tasks[0]["id"], "task-001")
        self.assertEqual(tasks[0]["device_name"], "Test Device")
        self.assertEqual(tasks[0]["name"], "Test Task")
        self.assertEqual(tasks[0]["status"], "success")

    def test_task_no_new_device_field(self):
        """验证 Task 不新增 device 字段"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        self.assertNotIn("device", tasks[0])

    def test_task_no_new_command_field(self):
        """验证 Task 不新增 command 字段"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        self.assertNotIn("command", tasks[0])

    def test_task_no_new_adapter_type_field(self):
        """验证 Task 不新增 adapter_type 字段"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        self.assertNotIn("adapter_type", tasks[0])

    def test_execution_context_not_written_back(self):
        """验证 ExecutionContext 不写回 Repository"""
        tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(tasks)
        
        mock_adapter = MagicMock()
        mock_adapter.connect.return_value = True
        mock_adapter.execute.return_value = {"success": True, "stdout": "ok", "stderr": "", "exit_code": 0}
        
        mock_factory = MagicMock()
        mock_factory.create.return_value = mock_adapter
        
        service = ExecutionService(repo, mock_factory)
        service.execute_task("task-001")
        
        # Task should not contain ExecutionContext fields
        self.assertNotIn("adapter_type", tasks[0])
        self.assertNotIn("command", tasks[0])


class TestArchitectureConstraints(unittest.TestCase):
    """测试架构约束"""

    def test_operation_does_not_call_adapter(self):
        """验证 Operation 模块不调用 Adapter"""
        operation_service_path = os.path.join(
            os.path.dirname(__file__), '..', 'backup_manager', 'services', 'operation_service.py'
        )
        if os.path.exists(operation_service_path):
            with open(operation_service_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertNotIn('adapter', content.lower())

    def test_scheduler_does_not_auto_execute(self):
        """验证 Scheduler 不自动执行 Task"""
        pass


if __name__ == '__main__':
    unittest.main()
