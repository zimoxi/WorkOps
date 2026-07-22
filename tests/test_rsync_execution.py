"""
WorkOps Rsync Real Execution Tests
Sprint034: Rsync Real Execution Layer

覆盖：
- ProcessResult validation
- SystemProcessRunner
- RsyncExecutor runtime integration
- Timeout handling
- Error mapping
- Security boundary
"""

import unittest
from unittest.mock import MagicMock, patch
import subprocess

from backup_manager.backup.process_result import ProcessResult
from backup_manager.backup.system_process import SystemProcessRunner
from backup_manager.backup.rsync_executor import RsyncExecutor
from backup_manager.backup.rsync import RsyncCommand
from backup_manager.backup.executor_result import ExecutorResult
from backup_manager.backup.execution import BackupExecution
from backup_manager.backup.process import ProcessRunner
from backup_manager.backup.errors import (
    ProcessExecutionError,
    RsyncExecutionFailedError,
    ExecutionTimeoutError,
    BackupWorkflowError,
)


# ============================================================================
# ProcessResult
# ============================================================================

class TestProcessResult(unittest.TestCase):
    """进程结果测试"""

    def test_valid_result(self):
        result = ProcessResult(exit_code=0, stdout="ok", stderr="", duration=1.5)
        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "ok")
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.duration, 1.5)
        self.assertTrue(result.success)

    def test_failed_result(self):
        result = ProcessResult(exit_code=1, stdout="", stderr="error", duration=0.5)
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)

    def test_frozen(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        with self.assertRaises(AttributeError):
            result.exit_code = 1

    def test_slots(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_exit_code_must_be_int(self):
        with self.assertRaises(ProcessExecutionError):
            ProcessResult(exit_code="0", stdout="", stderr="", duration=0)

    def test_exit_code_bool_rejected(self):
        with self.assertRaises(ProcessExecutionError):
            ProcessResult(exit_code=True, stdout="", stderr="", duration=0)

    def test_stdout_must_be_str(self):
        with self.assertRaises(ProcessExecutionError):
            ProcessResult(exit_code=0, stdout=123, stderr="", duration=0)

    def test_stderr_must_be_str(self):
        with self.assertRaises(ProcessExecutionError):
            ProcessResult(exit_code=0, stdout="", stderr=123, duration=0)

    def test_duration_must_be_number(self):
        with self.assertRaises(ProcessExecutionError):
            ProcessResult(exit_code=0, stdout="", stderr="", duration="slow")

    def test_duration_bool_rejected(self):
        with self.assertRaises(ProcessExecutionError):
            ProcessResult(exit_code=0, stdout="", stderr="", duration=True)

    def test_no_forbidden_fields(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        for attr in ["password", "credential", "token", "secret"]:
            self.assertFalse(hasattr(result, attr))

    def test_repr_no_secrets(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# SystemProcessRunner
# ============================================================================

class TestSystemProcessRunner(unittest.TestCase):
    """系统进程运行器测试"""

    def test_is_process_runner(self):
        runner = SystemProcessRunner()
        self.assertIsInstance(runner, ProcessRunner)

    def test_has_run(self):
        runner = SystemProcessRunner()
        self.assertTrue(hasattr(runner, "run"))

    def test_has_run_query(self):
        runner = SystemProcessRunner()
        self.assertTrue(hasattr(runner, "run_query"))

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr=""
        )
        runner = SystemProcessRunner()
        result = runner.run(["echo", "hello"])
        self.assertTrue(result.success)
        self.assertEqual(result.exit_code, 0)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="error"
        )
        runner = SystemProcessRunner()
        result = runner.run(["false"])
        self.assertFalse(result.success)
        self.assertEqual(result.exit_code, 1)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="test", timeout=5)
        runner = SystemProcessRunner()
        with self.assertRaises(ExecutionTimeoutError):
            runner.run(["sleep", "100"], timeout=5)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_command_not_found(self, mock_run):
        mock_run.side_effect = FileNotFoundError()
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run(["nonexistent_command"])

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_permission_denied(self, mock_run):
        mock_run.side_effect = PermissionError()
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run(["/root/secret"])

    def test_run_non_list_rejected(self):
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run("not a list")

    def test_run_non_string_arg_rejected(self):
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run([123, "hello"])

    def test_run_invalid_timeout_rejected(self):
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run(["echo"], timeout=0)

    def test_run_negative_timeout_rejected(self):
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run(["echo"], timeout=-1)

    def test_run_bool_timeout_rejected(self):
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run(["echo"], timeout=True)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_query_delegates(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ok", stderr=""
        )
        runner = SystemProcessRunner()
        result = runner.run_query(("echo", "hello"), timeout=30)
        self.assertTrue(result.success)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_shell_false(self, mock_run):
        """确认 shell=False"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr=""
        )
        runner = SystemProcessRunner()
        runner.run(["echo", "hello"])
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args
        self.assertFalse(call_kwargs.kwargs.get("shell", True))


# ============================================================================
# RsyncExecutor Runtime Integration
# ============================================================================

class TestRsyncExecutorRuntime(unittest.TestCase):
    """rsync 执行器运行时集成测试"""

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_success(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr=""
        )
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd)
        self.assertTrue(result.success)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="permission denied"
        )
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd)
        self.assertFalse(result.success)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd="rsync", timeout=5)
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd, timeout=5)
        self.assertFalse(result.success)

    def test_execute_rsync_no_runner(self):
        executor = RsyncExecutor()
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd)
        self.assertFalse(result.success)
        self.assertIn("No process runner", result.message)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_build_command_uses_rsync(self, mock_run):
        """确认 build_command 生成正确的 rsync 命令"""
        mock_run.return_value = MagicMock(
            returncode=0, stdout="", stderr=""
        )
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/", options=("-avz",))
        args = executor.build_command(cmd)
        self.assertEqual(args[0], "rsync")
        self.assertIn("-avz", args)
        self.assertIn("/data/", args)
        self.assertIn("/backup/", args)


# ============================================================================
# Error Model
# ============================================================================

class TestRsyncExecutionErrors(unittest.TestCase):
    """错误模型测试"""

    def test_process_execution_error(self):
        with self.assertRaises(BackupWorkflowError):
            raise ProcessExecutionError("test")

    def test_rsync_failed_error(self):
        exc = RsyncExecutionFailedError(exit_code=1, stderr="error")
        self.assertIn("1", str(exc))

    def test_rsync_failed_no_stderr(self):
        exc = RsyncExecutionFailedError(exit_code=2)
        self.assertIn("2", str(exc))

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (ProcessExecutionError, ("test",)),
            (RsyncExecutionFailedError, (1, "error")),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_process_result_no_credentials(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        for attr in ["password", "credential", "token", "secret"]:
            self.assertFalse(hasattr(result, attr))

    def test_system_runner_no_credentials(self):
        runner = SystemProcessRunner()
        for attr in ["password", "credential", "token", "secret"]:
            self.assertFalse(hasattr(runner, attr))

    def test_no_shell_true_in_source(self):
        """确认源码中没有 shell=True（排除注释和 shell=False）"""
        import ast
        with open("backup_manager/backup/system_process.py") as f:
            tree = ast.parse(f.read())
        for node in ast.walk(tree):
            if isinstance(node, ast.keyword):
                if node.arg == "shell" and isinstance(node.value, ast.Constant) and node.value.value is True:
                    self.fail("shell=True found in subprocess.run call")

    def test_no_exec_eval(self):
        import ast
        for filename in ["system_process.py", "process_result.py"]:
            filepath = f"backup_manager/backup/{filename}"
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_subprocess_run_with_list(self):
        """确认 subprocess.run 使用 list 参数"""
        with open("backup_manager/backup/system_process.py") as f:
            src = f.read()
        # 确认使用 list(command) 而非字符串
        self.assertIn("list(command)", src)

    def test_no_command_string_concatenation(self):
        """确认没有命令字符串拼接"""
        with open("backup_manager/backup/system_process.py") as f:
            src = f.read()
        # 检查常见的危险模式
        self.assertNotIn("os.system", src)
        self.assertNotIn("os.popen", src)
        self.assertNotIn("+ \" \" +", src)

    def test_error_messages_safe(self):
        try:
            raise RsyncExecutionFailedError(1, "test error")
        except RsyncExecutionFailedError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Extended ProcessResult Tests
# ============================================================================

class TestProcessResultExtended(unittest.TestCase):
    """进程结果扩展测试"""

    def test_success_exit_codes(self):
        for code in [0]:
            result = ProcessResult(exit_code=code, stdout="", stderr="", duration=0)
            self.assertTrue(result.success)

    def test_failure_exit_codes(self):
        for code in [1, 2, 126, 127, 130]:
            result = ProcessResult(exit_code=code, stdout="", stderr="", duration=0)
            self.assertFalse(result.success)

    def test_large_duration(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=3600.5)
        self.assertEqual(result.duration, 3600.5)

    def test_zero_duration(self):
        result = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        self.assertEqual(result.duration, 0)

    def test_stdout_content(self):
        result = ProcessResult(exit_code=0, stdout="file1\nfile2\n", stderr="", duration=1)
        self.assertIn("file1", result.stdout)

    def test_stderr_content(self):
        result = ProcessResult(exit_code=1, stdout="", stderr="permission denied", duration=1)
        self.assertIn("permission denied", result.stderr)


# ============================================================================
# Extended SystemProcessRunner Tests
# ============================================================================

class TestSystemProcessRunnerExtended(unittest.TestCase):
    """系统进程运行器扩展测试"""

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_captures_stdout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="output", stderr="")
        runner = SystemProcessRunner()
        result = runner.run(["echo", "hello"])
        self.assertEqual(result.stdout, "output")

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_captures_stderr(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="err")
        runner = SystemProcessRunner()
        result = runner.run(["false"])
        self.assertEqual(result.stderr, "err")

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_passes_timeout(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        runner.run(["echo"], timeout=60)
        call_kwargs = mock_run.call_args
        self.assertEqual(call_kwargs.kwargs.get("timeout"), 60)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_passes_capture_output(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        runner.run(["echo"])
        call_kwargs = mock_run.call_args
        self.assertTrue(call_kwargs.kwargs.get("capture_output"))

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_passes_text(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        runner.run(["echo"])
        call_kwargs = mock_run.call_args
        self.assertTrue(call_kwargs.kwargs.get("text"))

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_os_error(self, mock_run):
        mock_run.side_effect = OSError("disk error")
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run(["echo"])

    def test_run_empty_list(self):
        runner = SystemProcessRunner()
        with self.assertRaises(ProcessExecutionError):
            runner.run([])

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_run_tuple_command(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        result = runner.run(("echo", "hello"))
        self.assertTrue(result.success)


# ============================================================================
# Extended RsyncExecutor Tests
# ============================================================================

class TestRsyncExecutorExtended(unittest.TestCase):
    """rsync 执行器扩展测试"""

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_with_options(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/", options=("-avz", "--delete"))
        result = executor.execute_rsync(cmd)
        self.assertTrue(result.success)

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_result_is_executor_result(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd)
        self.assertIsInstance(result, ExecutorResult)

    def test_build_command_with_many_options(self):
        executor = RsyncExecutor()
        cmd = RsyncCommand(
            source="/data/", target="/backup/",
            options=("-avz", "--delete", "--exclude=.git"),
        )
        args = executor.build_command(cmd)
        self.assertEqual(len(args), 6)  # rsync + 3 options + source + target

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_failure_has_message(self, mock_run):
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="error msg")
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd)
        self.assertFalse(result.success)
        self.assertIn("error msg", result.message)

    def test_registry_integration(self):
        from backup_manager.backup.executor_registry import BackupExecutorRegistry
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        registry = BackupExecutorRegistry()
        registry.register("rsync", executor)
        self.assertTrue(registry.supports("rsync"))

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_exit_code_preserved(self, mock_run):
        mock_run.return_value = MagicMock(returncode=23, stdout="", stderr="partial transfer")
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        result = executor.execute_rsync(cmd)
        self.assertFalse(result.success)

    def test_build_command_no_options(self):
        executor = RsyncExecutor()
        cmd = RsyncCommand(source="/src/", target="/dst/")
        args = executor.build_command(cmd)
        self.assertEqual(args, ["rsync", "/src/", "/dst/"])

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_execute_rsync_calls_subprocess(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
        runner = SystemProcessRunner()
        executor = RsyncExecutor(process_runner=runner)
        cmd = RsyncCommand(source="/data/", target="/backup/")
        executor.execute_rsync(cmd)
        mock_run.assert_called_once()

    @patch("backup_manager.backup.system_process.subprocess.run")
    def test_system_runner_returns_process_result(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        runner = SystemProcessRunner()
        result = runner.run(["echo"])
        self.assertIsInstance(result, ProcessResult)

    def test_process_result_success_property(self):
        r0 = ProcessResult(exit_code=0, stdout="", stderr="", duration=0)
        r1 = ProcessResult(exit_code=1, stdout="", stderr="", duration=0)
        self.assertTrue(r0.success)
        self.assertFalse(r1.success)

    def test_rsync_execution_error_hierarchy(self):
        self.assertTrue(issubclass(ProcessExecutionError, BackupWorkflowError))
        self.assertTrue(issubclass(RsyncExecutionFailedError, BackupWorkflowError))

    def test_system_runner_is_process_runner_subclass(self):
        self.assertTrue(issubclass(SystemProcessRunner, ProcessRunner))

    def test_rsync_execution_failed_error_default(self):
        exc = RsyncExecutionFailedError()
        self.assertIn("-1", str(exc))


if __name__ == "__main__":
    unittest.main()
