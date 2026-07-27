"""
WorkOps Backup Runtime Dispatcher — 备份运行时分发器
Sprint070: Real Backup Execution Engine

Routes backup requests to appropriate runtime handlers.
"""

from .model import BackupExecutionRequest, BackupExecutionMode
from .result import BackupExecutionResult
from .handlers import LinuxBackupHandler, PVEBackupHandler, OMVBackupHandler
from .errors import BackupRuntimeUnavailableError


class BackupRuntimeDispatcher:
    """
    备份运行时分发器。

    路由:
    LINUX -> LinuxBackupHandler
    PVE   -> PVEBackupHandler
    OMV   -> OMVBackupHandler

    拒绝: 未知运行时
    """

    def __init__(
        self,
        linux_handler: LinuxBackupHandler | None = None,
        pve_handler: PVEBackupHandler | None = None,
        omv_handler: OMVBackupHandler | None = None,
    ):
        self._handlers = {
            BackupExecutionMode.LINUX: linux_handler,
            BackupExecutionMode.PVE: pve_handler,
            BackupExecutionMode.OMV: omv_handler,
        }

    def dispatch(self, request: BackupExecutionRequest) -> BackupExecutionResult:
        """
        分发备份请求到对应的运行时处理器。

        Args:
            request: 备份执行请求

        Returns:
            BackupExecutionResult

        Raises:
            BackupRuntimeUnavailableError: 运行时不可用
        """
        handler = self._handlers.get(request.mode)
        if handler is None:
            raise BackupRuntimeUnavailableError(
                f"No handler registered for mode: {request.mode.value}"
            )
        return handler.execute(request)
