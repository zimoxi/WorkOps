"""
WorkOps Rsync Command Model — rsync 命令模型
Sprint033: Rsync Executor Foundation

frozen dataclass。不包含密码/凭证。
"""

from dataclasses import dataclass

from .errors import InvalidRsyncCommandError


@dataclass(frozen=True, slots=True)
class RsyncCommand:
    """
    rsync 命令。不可变。

    只描述 source/target/options，不包含命令字符串。
    """

    source: str
    target: str
    options: tuple = ()

    def __post_init__(self):
        if not isinstance(self.source, str) or not self.source.strip():
            raise InvalidRsyncCommandError("source must be a non-empty string")
        if not isinstance(self.target, str) or not self.target.strip():
            raise InvalidRsyncCommandError("target must be a non-empty string")
        if not isinstance(self.options, tuple):
            raise InvalidRsyncCommandError("options must be a tuple")
        for opt in self.options:
            if not isinstance(opt, str) or not opt.strip():
                raise InvalidRsyncCommandError("all options must be non-empty strings")
