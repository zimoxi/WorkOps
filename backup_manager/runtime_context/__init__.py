"""
WorkOps Runtime Context Domain — 运行时上下文域
Sprint051: Adapter Execution Context Foundation
"""

from .errors import (
    ExecutionContextError,
    InvalidExecutionContextError,
    ExecutionContextConflictError,
)
from .model import ExecutionMode
from .metadata import ExecutionMetadata
from .context import ExecutionContext, AdapterRuntimeContext, validate_execution_context

__all__ = [
    "ExecutionContextError",
    "InvalidExecutionContextError",
    "ExecutionContextConflictError",
    "ExecutionMode",
    "ExecutionMetadata",
    "ExecutionContext",
    "AdapterRuntimeContext",
    "validate_execution_context",
]
