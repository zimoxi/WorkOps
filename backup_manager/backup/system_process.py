"""
WorkOps System Process Runner — 系统进程运行器
Sprint034: Rsync Real Execution Layer

使用 subprocess.run + argument list。
禁止 shell=True。
"""

import subprocess
import time

from .process import ProcessRunner
from .process_result import ProcessResult
from .errors import ProcessExecutionError, ExecutionTimeoutError


class SystemProcessRunner(ProcessRunner):
    """
    系统进程运行器。

    使用 subprocess.run + argument list。
    禁止 shell=True。
    """

    def run(self, command, timeout: int = 300) -> ProcessResult:
        """
        运行命令。

        Args:
            command: 命令参数列表 (list[str] 或 tuple[str,...])
            timeout: 超时秒数

        Returns:
            ProcessResult
        """
        if not isinstance(command, (list, tuple)):
            raise ProcessExecutionError("command must be a list or tuple")
        for arg in command:
            if not isinstance(arg, str):
                raise ProcessExecutionError("all arguments must be strings")
        if not isinstance(timeout, int) or isinstance(timeout, bool) or timeout <= 0:
            raise ProcessExecutionError("timeout must be a positive integer")

        start = time.monotonic()
        try:
            result = subprocess.run(
                list(command),
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False,
            )
            duration = time.monotonic() - start
            return ProcessResult(
                exit_code=result.returncode,
                stdout=result.stdout,
                stderr=result.stderr,
                duration=duration,
            )
        except subprocess.TimeoutExpired:
            duration = time.monotonic() - start
            raise ExecutionTimeoutError(f"Process timed out after {timeout}s")
        except FileNotFoundError:
            duration = time.monotonic() - start
            raise ProcessExecutionError("Command not found")
        except PermissionError:
            duration = time.monotonic() - start
            raise ProcessExecutionError("Permission denied")
        except OSError as e:
            duration = time.monotonic() - start
            raise ProcessExecutionError(f"OS error: {type(e).__name__}")

    def run_query(self, arguments: tuple, timeout: int = 300) -> ProcessResult:
        """
        运行查询命令（兼容接口）。

        Args:
            arguments: 命令参数元组
            timeout: 超时秒数

        Returns:
            ProcessResult
        """
        return self.run(arguments, timeout=timeout)
