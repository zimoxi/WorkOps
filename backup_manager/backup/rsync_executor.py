"""
WorkOps Rsync Executor — rsync 执行器
Sprint033: Rsync Executor Foundation

executor_type: "rsync"
使用 ProcessRunner 接口。不直接调用 subprocess。
"""

from .executor import BackupExecutor
from .executor_result import ExecutorResult
from .execution import BackupExecution
from .rsync import RsyncCommand
from .process import ProcessRunner
from .errors import RsyncExecutorError


class RsyncExecutor(BackupExecutor):
    """
    rsync 执行器。

    使用 ProcessRunner 接口。不直接调用 subprocess。
    """

    executor_type = "rsync"

    def __init__(self, process_runner: ProcessRunner = None):
        self._runner = process_runner

    def execute(self, execution: BackupExecution) -> ExecutorResult:
        """
        执行备份。

        Args:
            execution: 执行记录

        Returns:
            ExecutorResult
        """
        if self._runner is None:
            return ExecutorResult(
                success=False,
                message="No process runner configured",
            )
        try:
            result = self._runner.run(execution)
            return ExecutorResult(
                success=result.get("success", False),
                message=result.get("message", ""),
            )
        except Exception as e:
            return ExecutorResult(
                success=False,
                message=f"Execution failed: {type(e).__name__}",
            )

    def build_command(self, rsync_command: RsyncCommand) -> list[str]:
        """
        构建 rsync 命令参数列表。

        Args:
            rsync_command: rsync 命令

        Returns:
            list[str]: 命令参数列表
        """
        cmd = ["rsync"]
        cmd.extend(rsync_command.options)
        cmd.append(rsync_command.source)
        cmd.append(rsync_command.target)
        return cmd
