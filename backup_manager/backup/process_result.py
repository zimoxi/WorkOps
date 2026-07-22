"""
WorkOps Process Result — 进程结果模型
Sprint034: Rsync Real Execution Layer

frozen dataclass。不包含 credential。
"""

from dataclasses import dataclass

from .errors import ProcessExecutionError


@dataclass(frozen=True, slots=True)
class ProcessResult:
    """
    进程执行结果。不可变。
    """

    exit_code: int
    stdout: str
    stderr: str
    duration: float

    def __post_init__(self):
        if not isinstance(self.exit_code, int) or isinstance(self.exit_code, bool):
            raise ProcessExecutionError("exit_code must be an integer")
        if not isinstance(self.stdout, str):
            raise ProcessExecutionError("stdout must be a string")
        if not isinstance(self.stderr, str):
            raise ProcessExecutionError("stderr must be a string")
        if not isinstance(self.duration, (int, float)) or isinstance(self.duration, bool):
            raise ProcessExecutionError("duration must be a number")

    @property
    def success(self) -> bool:
        return self.exit_code == 0
