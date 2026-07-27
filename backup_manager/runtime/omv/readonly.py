"""
WorkOps OMV ReadOnly Executor — OMV 只读执行器
Sprint069: Real OMV API Client

只定义接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .exceptions import OMVReadonlyViolationError

# Allowed read-only operations
ALLOWED_READONLY_OPERATIONS = frozenset({
    "system_info",
    "storage_status",
    "service_status",
})

# Forbidden patterns
FORBIDDEN_PATTERNS = frozenset({
    "create",
    "delete",
    "update",
    "set",
    "modify",
    "write",
    "upload",
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


def validate_omv_readonly_operation(operation: str) -> None:
    """
    验证 OMV 只读操作。

    Args:
        operation: 操作标识符

    Raises:
        OMVReadonlyViolationError: 操作不是只读的
    """
    if not isinstance(operation, str) or not operation.strip():
        raise OMVReadonlyViolationError("operation must be a non-empty string")
    op_lower = operation.lower().strip()
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in op_lower:
            raise OMVReadonlyViolationError(f"operation contains forbidden pattern: {pattern}")


class OMVReadOnlyExecutor(ABC):
    """
    OMV 只读执行器接口。

    允许的操作: system_info, storage_status, service_status
    禁止: create, delete, update, set, modify, write, upload, shell
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
            OMVReadonlyViolationError: 操作不是只读的
        """
        ...
