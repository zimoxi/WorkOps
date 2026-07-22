"""
WorkOps Rsync Executor Tests
Sprint033: Rsync Executor Foundation

覆盖：
- RsyncCommand validation
- ProcessRunner contract
- RsyncExecutor integration
- Registry integration
- Error model
- Security boundary
"""

import unittest

from backup_manager.backup.rsync import RsyncCommand
from backup_manager.backup.process import ProcessRunner
from backup_manager.backup.rsync_executor import RsyncExecutor
from backup_manager.backup.executor import BackupExecutor
from backup_manager.backup.executor_result import ExecutorResult
from backup_manager.backup.executor_registry import BackupExecutorRegistry
from backup_manager.backup.execution import BackupExecution
from backup_manager.backup.errors import (
    RsyncExecutorError,
    InvalidRsyncCommandError,
    BackupWorkflowError,
)


# ============================================================================
# RsyncCommand
# ============================================================================

class TestRsyncCommand(unittest.TestCase):
    """rsync 命令模型测试"""

    def test_valid_command(self):
        cmd = RsyncCommand(source="/data/", target="/backup/")
        self.assertEqual(cmd.source, "/data/")
        self.assertEqual(cmd.target, "/backup/")
        self.assertEqual(cmd.options, ())

    def test_with_options(self):
        cmd = RsyncCommand(
            source="/data/",
            target="/backup/",
            options=("-avz", "--delete"),
        )
        self.assertEqual(len(cmd.options), 2)
        self.assertIn("-avz", cmd.options)

    def test_frozen(self):
        cmd = RsyncCommand(source="/data/", target="/backup/")
        with self.assertRaises(AttributeError):
            cmd.source = "other"

    def test_slots(self):
        cmd = RsyncCommand(source="/data/", target="/backup/")
        with self.assertRaises(AttributeError):
            cmd.__dict__

    def test_empty_source_rejected(self):
        with self.assertRaises(InvalidRsyncCommandError):
            RsyncCommand(source="", target="/backup/")

    def test_whitespace_source_rejected(self):
        with self.assertRaises(InvalidRsyncCommandError):
            RsyncCommand(source="   ", target="/backup/")

    def test_empty_target_rejected(self):
        with self.assertRaises(InvalidRsyncCommandError):
            RsyncCommand(source="/data/", target="")

    def test_options_must_be_tuple(self):
        with self.assertRaises(InvalidRsyncCommandError):
            RsyncCommand(source="/data/", target="/backup/", options=["-avz"])

    def test_empty_option_rejected(self):
        with self.assertRaises(InvalidRsyncCommandError):
            RsyncCommand(source="/data/", target="/backup/", options=("",))

    def test_whitespace_option_rejected(self):
        with self.assertRaises(InvalidRsyncCommandError):
            RsyncCommand(source="/data/", target="/backup/", options=("  ",))

    def test_no_forbidden_fields(self):
        cmd = RsyncCommand(source="/data/", target="/backup/")
        for attr in ["password", "credential", "token", "command", "secret"]:
            self.assertFalse(hasattr(cmd, attr))

    def test_repr_no_secrets(self):
        cmd = RsyncCommand(source="/data/", target="/backup/")
        r = repr(cmd)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# ProcessRunner Contract
# ============================================================================

class TestProcessRunnerContract(unittest.TestCase):
    """进程运行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(ProcessRunner, ABC))

    def test_has_run(self):
        self.assertTrue(hasattr(ProcessRunner, "run"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ProcessRunner()

    def test_concrete_subclass(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "ok"}
        runner = MockRunner()
        result = runner.run(RsyncCommand(source="/data/", target="/backup/"))
        self.assertTrue(result["success"])

    def test_missing_run(self):
        class BadRunner(ProcessRunner):
            pass
        with self.assertRaises(TypeError):
            BadRunner()


# ============================================================================
# RsyncExecutor
# ============================================================================

class TestRsyncExecutor(unittest.TestCase):
    """rsync 执行器测试"""

    def test_executor_type(self):
        executor = RsyncExecutor()
        self.assertEqual(executor.executor_type, "rsync")

    def test_is_backup_executor(self):
        executor = RsyncExecutor()
        self.assertIsInstance(executor, BackupExecutor)

    def test_execute_without_runner(self):
        executor = RsyncExecutor()
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertFalse(result.success)
        self.assertIn("No process runner", result.message)

    def test_execute_with_mock_runner(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "synced"}
        executor = RsyncExecutor(process_runner=MockRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertTrue(result.success)
        self.assertEqual(result.message, "synced")

    def test_execute_runner_failure(self):
        class FailRunner(ProcessRunner):
            def run(self, command):
                return {"success": False, "message": "permission denied"}
        executor = RsyncExecutor(process_runner=FailRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertFalse(result.success)
        self.assertIn("permission denied", result.message)

    def test_execute_runner_exception(self):
        class ErrorRunner(ProcessRunner):
            def run(self, command):
                raise OSError("disk full")
        executor = RsyncExecutor(process_runner=ErrorRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertFalse(result.success)
        self.assertIn("OSError", result.message)

    def test_build_command(self):
        executor = RsyncExecutor()
        cmd = RsyncCommand(
            source="/data/",
            target="/backup/",
            options=("-avz", "--delete"),
        )
        args = executor.build_command(cmd)
        self.assertEqual(args[0], "rsync")
        self.assertIn("-avz", args)
        self.assertIn("--delete", args)
        self.assertIn("/data/", args)
        self.assertIn("/backup/", args)

    def test_build_command_no_options(self):
        executor = RsyncExecutor()
        cmd = RsyncCommand(source="/data/", target="/backup/")
        args = executor.build_command(cmd)
        self.assertEqual(args, ["rsync", "/data/", "/backup/"])

    def test_no_forbidden_methods(self):
        executor = RsyncExecutor()
        for method in ["execute_shell", "run_shell", "exec_command"]:
            self.assertFalse(hasattr(executor, method))


# ============================================================================
# Registry Integration
# ============================================================================

class TestRsyncRegistryIntegration(unittest.TestCase):
    """注册表集成测试"""

    def test_register_to_registry(self):
        registry = BackupExecutorRegistry()
        executor = RsyncExecutor()
        registry.register("rsync", executor)
        self.assertTrue(registry.supports("rsync"))

    def test_get_from_registry(self):
        registry = BackupExecutorRegistry()
        executor = RsyncExecutor()
        registry.register("rsync", executor)
        got = registry.get("rsync")
        self.assertIs(got, executor)

    def test_execute_via_registry(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "ok"}
        registry = BackupExecutorRegistry()
        executor = RsyncExecutor(process_runner=MockRunner())
        registry.register("rsync", executor)
        got = registry.get("rsync")
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = got.execute(execution)
        self.assertTrue(result.success)


# ============================================================================
# Error Model
# ============================================================================

class TestRsyncErrorModel(unittest.TestCase):
    """错误模型测试"""

    def test_rsync_executor_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise RsyncExecutorError("test")

    def test_invalid_command_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise InvalidRsyncCommandError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (RsyncExecutorError, ("test",)),
            (InvalidRsyncCommandError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "command"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_rsync_command_no_credentials(self):
        cmd = RsyncCommand(source="/data/", target="/backup/")
        for attr in ["password", "credential", "token", "secret", "command"]:
            self.assertFalse(hasattr(cmd, attr))

    def test_executor_no_credentials(self):
        executor = RsyncExecutor()
        for attr in ["password", "credential", "token", "secret"]:
            self.assertFalse(hasattr(executor, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["rsync.py", "process.py", "rsync_executor.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
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
        for filename in ["rsync.py", "process.py", "rsync_executor.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_no_shell_true(self):
        """确认没有 shell=True"""
        import ast
        import os
        for filename in ["rsync.py", "process.py", "rsync_executor.py"]:
            filepath = os.path.join("backup_manager", "backup", filename)
            with open(filepath) as f:
                src = f.read()
            self.assertNotIn("shell=True", src)
            self.assertNotIn("shell = True", src)

    def test_build_command_no_shell(self):
        """build_command 返回列表，不是字符串"""
        executor = RsyncExecutor()
        cmd = RsyncCommand(source="/data/", target="/backup/", options=("-avz",))
        args = executor.build_command(cmd)
        self.assertIsInstance(args, list)
        for arg in args:
            self.assertIsInstance(arg, str)

    def test_process_runner_no_subprocess_import(self):
        """ProcessRunner 接口文件不导入 subprocess"""
        import ast
        with open("backup_manager/backup/process.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "subprocess")
            elif isinstance(node, ast.ImportFrom):
                if node.module and "subprocess" in node.module:
                    self.fail("subprocess imported in process.py")

    def test_error_messages_safe(self):
        """错误消息不包含敏感信息"""
        try:
            raise RsyncExecutorError("test")
        except RsyncExecutorError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Extended RsyncCommand Tests
# ============================================================================

class TestRsyncCommandExtended(unittest.TestCase):
    """rsync 命令扩展测试"""

    def test_multiple_options(self):
        cmd = RsyncCommand(
            source="/data/", target="/backup/",
            options=("-avz", "--delete", "--exclude=.git", "--progress"),
        )
        self.assertEqual(len(cmd.options), 4)

    def test_single_option(self):
        cmd = RsyncCommand(source="/data/", target="/backup/", options=("-a",))
        self.assertEqual(len(cmd.options), 1)

    def test_remote_source(self):
        cmd = RsyncCommand(source="user@host:/data/", target="/backup/")
        self.assertIn("@", cmd.source)

    def test_remote_target(self):
        cmd = RsyncCommand(source="/data/", target="user@host:/backup/")
        self.assertIn("@", cmd.target)

    def test_command_args_format(self):
        """build_command 返回列表格式正确"""
        executor = RsyncExecutor()
        cmd = RsyncCommand(source="/data/", target="/backup/", options=("-avz",))
        args = executor.build_command(cmd)
        self.assertEqual(args[0], "rsync")
        self.assertEqual(args[-1], "/backup/")
        self.assertEqual(args[-2], "/data/")


# ============================================================================
# Extended ProcessRunner Tests
# ============================================================================

class TestProcessRunnerExtended(unittest.TestCase):
    """进程运行器扩展测试"""

    def test_runner_returns_dict(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "ok"}
        runner = MockRunner()
        result = runner.run(RsyncCommand(source="/a/", target="/b/"))
        self.assertIsInstance(result, dict)

    def test_runner_failure_result(self):
        class FailRunner(ProcessRunner):
            def run(self, command):
                return {"success": False, "message": "error"}
        runner = FailRunner()
        result = runner.run(RsyncCommand(source="/a/", target="/b/"))
        self.assertFalse(result["success"])


# ============================================================================
# Extended RsyncExecutor Tests
# ============================================================================

class TestRsyncExecutorExtended(unittest.TestCase):
    """rsync 执行器扩展测试"""

    def test_execute_returns_executor_result(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "ok"}
        executor = RsyncExecutor(process_runner=MockRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertIsInstance(result, ExecutorResult)

    def test_execute_preserves_message(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "transferred 100 files"}
        executor = RsyncExecutor(process_runner=MockRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertEqual(result.message, "transferred 100 files")

    def test_build_command_preserves_order(self):
        executor = RsyncExecutor()
        cmd = RsyncCommand(source="/src/", target="/dst/", options=("-a", "-v"))
        args = executor.build_command(cmd)
        self.assertEqual(args[0], "rsync")
        # options come before source/target
        self.assertEqual(args[-2], "/src/")
        self.assertEqual(args[-1], "/dst/")

    def test_executor_with_none_runner_default(self):
        executor = RsyncExecutor()
        self.assertIsNone(executor._runner)

    def test_executor_type_is_string(self):
        executor = RsyncExecutor()
        self.assertIsInstance(executor.executor_type, str)

    def test_multiple_executions(self):
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "ok"}
        executor = RsyncExecutor(process_runner=MockRunner())
        for i in range(5):
            execution = BackupExecution(execution_id=f"e{i}", job_id=f"j{i}")
            result = executor.execute(execution)
            self.assertTrue(result.success)

    def test_registry_integration_full(self):
        """完整注册表集成"""
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "ok"}
        registry = BackupExecutorRegistry()
        executor = RsyncExecutor(process_runner=MockRunner())
        registry.register("rsync", executor)
        self.assertTrue(registry.supports("rsync"))
        self.assertEqual(len(registry.list()), 1)
        got = registry.get("rsync")
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = got.execute(execution)
        self.assertTrue(result.success)

    def test_rsync_command_error_no_secrets(self):
        try:
            raise InvalidRsyncCommandError("bad source")
        except InvalidRsyncCommandError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_rsync_command_empty_tuple_options(self):
        """空 tuple options 允许"""
        cmd = RsyncCommand(source="/data/", target="/backup/", options=())
        self.assertEqual(len(cmd.options), 0)

    def test_executor_build_command_with_many_options(self):
        """多个 options 正确拼接"""
        executor = RsyncExecutor()
        cmd = RsyncCommand(
            source="/data/", target="/backup/",
            options=("-avz", "--delete", "--exclude=.git", "--progress", "-e", "ssh"),
        )
        args = executor.build_command(cmd)
        # rsync + 6 options + source + target = 9
        self.assertEqual(len(args), 9)
        self.assertEqual(args[0], "rsync")
        self.assertIn("-avz", args)
        self.assertIn("ssh", args)
        self.assertEqual(args[-2], "/data/")
        self.assertEqual(args[-1], "/backup/")

    def test_rsync_executor_no_shell_in_source(self):
        """source 不包含 shell 元字符"""
        cmd = RsyncCommand(source="/data/", target="/backup/")
        for char in [";", "|", "&", "$", "`", "\n"]:
            self.assertNotIn(char, cmd.source)
            self.assertNotIn(char, cmd.target)

    def test_rsync_executor_result_has_message(self):
        """结果必须有 message 字段"""
        class MockRunner(ProcessRunner):
            def run(self, command):
                return {"success": True, "message": "done"}
        executor = RsyncExecutor(process_runner=MockRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertTrue(hasattr(result, "message"))
        self.assertEqual(result.message, "done")

    def test_rsync_executor_runner_missing_keys(self):
        """runner 返回缺少 keys 时使用默认值"""
        class SparseRunner(ProcessRunner):
            def run(self, command):
                return {}
        executor = RsyncExecutor(process_runner=SparseRunner())
        execution = BackupExecution(execution_id="e1", job_id="j1")
        result = executor.execute(execution)
        self.assertFalse(result.success)
        self.assertEqual(result.message, "")


if __name__ == "__main__":
    unittest.main()
