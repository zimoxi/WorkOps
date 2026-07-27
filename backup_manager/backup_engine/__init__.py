"""
WorkOps Backup Engine Domain — 备份引擎域
Sprint070: Real Backup Execution Engine
"""

from .errors import (
    BackupEngineError,
    InvalidBackupExecutionError,
    BackupRuntimeUnavailableError,
    BackupExecutionTimeoutError,
)
from .model import BackupExecutionMode, BackupExecutionRequest
from .result import BackupExecutionResult
from .handlers import LinuxBackupHandler, PVEBackupHandler, OMVBackupHandler
from .dispatcher import BackupRuntimeDispatcher
from .executor import RealBackupExecutor

__all__ = [
    "BackupEngineError",
    "InvalidBackupExecutionError",
    "BackupRuntimeUnavailableError",
    "BackupExecutionTimeoutError",
    "BackupExecutionMode",
    "BackupExecutionRequest",
    "BackupExecutionResult",
    "LinuxBackupHandler",
    "PVEBackupHandler",
    "OMVBackupHandler",
    "BackupRuntimeDispatcher",
    "RealBackupExecutor",
]
