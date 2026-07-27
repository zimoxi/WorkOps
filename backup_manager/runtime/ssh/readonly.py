"""
WorkOps ReadOnly SSH Executor — 只读 SSH 执行器
Sprint067: Real Linux SSH Connector

只定义接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .exceptions import SSHReadonlyViolationError

# Allowed read-only operations
ALLOWED_READONLY_OPERATIONS = frozenset({
    "system_info",
    "disk_info",
    "service_status",
})

# Forbidden patterns
FORBIDDEN_PATTERNS = frozenset({
    "shell",
    "script",
    "sudo",
    "rm ",
    "mv ",
    "cp ",
    "chmod",
    "chown",
    "mkfs",
    "dd ",
    ">",
    ">>",
    "|",
    ";",
    "&",
    "`",
    "$(",
})


def validate_readonly_operation(operation: str) -> None:
    """
    验证只读操作。

    Args:
        operation: 操作标识符

    Raises:
        SSHReadonlyViolationError: 操作不是只读的
    """
    if not isinstance(operation, str) or not operation.strip():
        raise SSHReadonlyViolationError("operation must be a non-empty string")
    op_lower = operation.lower().strip()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in op_lower:
            raise SSHReadonlyViolationError(f"operation contains forbidden pattern: {pattern}")


class ReadOnlySSHExecutor(ABC):
    """
    只读 SSH 执行器接口。

    允许的操作: system_info, disk_info, service_status
    禁止: shell, script, sudo, command injection, mutation
    """

    @abstractmethod
    def execute(self, operation: str) -> dict:
        """
        执行只读操作。

        Args:
            operation: 操作标识符

        Returns:
            dict with operation result

        Raises:
            SSHReadonlyViolationError: 操作不是只读的
        """
        ...
