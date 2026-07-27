"""
WorkOps PVE ReadOnly Executor — PVE 只读执行器
Sprint068: Real PVE API Client

只定义接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .exceptions import PVEReadonlyViolationError

# Allowed read-only operations
ALLOWED_READONLY_OPERATIONS = frozenset({
    "node_info",
    "vm_status",
    "storage_status",
})

# Forbidden patterns
FORBIDDEN_PATTERNS = frozenset({
    "create",
    "delete",
    "update",
    "set",
    "modify",
    "execute_command",
    "shell",
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


def validate_pve_readonly_operation(operation: str) -> None:
    """
    验证 PVE 只读操作。

    Args:
        operation: 操作标识符

    Raises:
        PVEReadonlyViolationError: 操作不是只读的
    """
    if not isinstance(operation, str) or not operation.strip():
        raise PVEReadonlyViolationError("operation must be a non-empty string")
    op_lower = operation.lower().strip()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in op_lower:
            raise PVEReadonlyViolationError(f"operation contains forbidden pattern: {pattern}")


class PVEReadOnlyExecutor(ABC):
    """
    PVE 只读执行器接口。

    允许的操作: node_info, vm_status, storage_status
    禁止: create, delete, update, set, modify, execute_command, shell
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
            PVEReadonlyViolationError: 操作不是只读的
        """
        ...
