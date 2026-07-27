"""
WorkOps Restore Runtime Dispatcher — 恢复运行时分发器
Sprint071: Real Restore Execution Engine

Routes restore requests to appropriate runtime handlers.
"""

from .model import RestoreExecutionRequest, RestoreExecutionMode
from .result import RestoreExecutionResult
from .handlers import LinuxRestoreHandler, PVERestoreHandler, OMVRestoreHandler
from .errors import RestoreRuntimeUnavailableError


class RestoreRuntimeDispatcher:
    """
    恢复运行时分发器。

    路由:
    LINUX -> LinuxRestoreHandler
    PVE   -> PVERestoreHandler
    OMV   -> OMVRestoreHandler

    拒绝: 未知运行时
    """

    def __init__(
        self,
        linux_handler: LinuxRestoreHandler | None = None,
        pve_handler: PVERestoreHandler | None = None,
        omv_handler: OMVRestoreHandler | None = None,
    ):
        self._handlers = {
            RestoreExecutionMode.LINUX: linux_handler,
            RestoreExecutionMode.PVE: pve_handler,
            RestoreExecutionMode.OMV: omv_handler,
        }

    def dispatch(self, request: RestoreExecutionRequest) -> RestoreExecutionResult:
        """
        分发恢复请求到对应的运行时处理器。

        Args:
            request: 恢复执行请求

        Returns:
            RestoreExecutionResult

        Raises:
            RestoreRuntimeUnavailableError: 运行时不可用
        """
        handler = self._handlers.get(request.mode)
        if handler is None:
            raise RestoreRuntimeUnavailableError(
                f"No handler registered for mode: {request.mode.value}"
            )
        return handler.execute(request)
