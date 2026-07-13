"""
WorkOps ExecutionService — 执行服务
Sprint018: Execution Engine Foundation

Task 是唯一执行入口。
禁止 Operation 直接调用 Adapter。
禁止 Scheduler 自动触发 Task。

执行链：
Task → ExecutionService → ExecutionContext → AdapterFactory.create("mock") → MockAdapter → ExecutionResult
"""

from datetime import datetime
from .errors import TaskNotFoundError, InvalidTaskStateError, TaskStateTransitionError
from .result import ExecutionResult
from .context import ExecutionContext
from ..adapters import AdapterFactory
from ..adapters.errors import (
    AdapterNotConnectedError,
    AdapterExecutionError,
    AdapterNotImplementedError,
)


class ExecutionService:
    """执行服务"""

    def __init__(self, task_repository, adapter_factory=None):
        """
        初始化 ExecutionService
        
        Args:
            task_repository: TaskRepository 实例
            adapter_factory: AdapterFactory 实例（默认使用 AdapterFactory）
        """
        self.task_repository = task_repository
        self.adapter_factory = adapter_factory or AdapterFactory

    def execute_task(self, task_id: str) -> ExecutionResult:
        """
        执行 Task（唯一入口）
        
        Args:
            task_id: Task ID
        
        Returns:
            ExecutionResult: 执行结果
        
        Raises:
            TaskNotFoundError: Task 不存在（前置错误）
            InvalidTaskStateError: Task 状态不是 pending（前置错误）
            TaskStateTransitionError: Task 状态转换失败（前置/最终错误）
        """
        # ─── 前置检查（直接抛出，不修改 Task 状态）────────
        
        # 1. 读取 Task
        task = self.task_repository.get_by_id(task_id)
        
        # 2. 检查 Task 是否存在
        if not task:
            raise TaskNotFoundError(task_id)
        
        # 3. 检查 Task 状态是否为 pending
        if task.get("status") != "pending":
            raise InvalidTaskStateError(task_id, task.get("status"))
        
        # 4. pending → running（检查返回值）
        transitioned = self.task_repository.transition_status(
            task_id, "pending", "running"
        )
        if not transitioned:
            raise TaskStateTransitionError(task_id, "pending", "running")
        
        # ─── 执行阶段 ────────────────────────────────────
        
        # 5. 变量初始化
        adapter = None
        connected = False
        adapter_result = None
        primary_error = None
        cleanup_error = None
        
        # 6. 创建 ExecutionContext（临时，不持久化）
        context = ExecutionContext(
            task_id=task_id,
            adapter_type="mock",
            device={"id": "mock-device", "name": task.get("device_name", "Mock Device")},
            command=f"mock-execute:{task_id}",
            started_at=datetime.now()
        )
        
        try:
            # 7. Adapter 创建（在 try 内）
            adapter = self.adapter_factory.create("mock")
            
            # 8. connect() 并检查返回值（必须严格返回 True）
            connected = adapter.connect(context.device)
            if connected is not True:
                connected = False
                raise AdapterNotConnectedError("connect() did not return True")
            
            # 9. execute()
            adapter_result = adapter.execute(context.command)
            
            # 10. 检查返回值结构
            if not isinstance(adapter_result, dict):
                raise AdapterExecutionError("Adapter reported execution failure")
            
            if not adapter_result.get("success"):
                raise AdapterExecutionError("Adapter reported execution failure")
            
        except Exception as error:
            primary_error = error
        
        # ─── disconnect（在 finally 中）──────────────────
        
        try:
            if connected and adapter is not None:
                adapter.disconnect()
        except Exception as error:
            cleanup_error = error
        
        # ─── 统一判断最终状态（在 disconnect 后）──────────
        
        finished_at = datetime.now()
        duration = str(finished_at - context.started_at)
        
        if primary_error is None and cleanup_error is None:
            # execute 成功 + disconnect 成功 → success
            final_status = "success"
            safe_message = "Execution completed"
            safe_stderr = adapter_result.get("stderr", "")
            exit_code = adapter_result.get("exit_code", 0)
            stdout = adapter_result.get("stdout", "")
        elif primary_error is not None:
            # execute 失败 → failed（保留主执行错误）
            final_status = "failed"
            safe_message = f"Execution failed: {type(primary_error).__name__}"
            safe_stderr = f"Error type: {type(primary_error).__name__}"
            exit_code = 1
            stdout = ""
        else:
            # execute 成功 + disconnect 失败 → failed
            final_status = "failed"
            safe_message = "Execution succeeded but disconnect failed"
            safe_stderr = f"Cleanup error: {type(cleanup_error).__name__}"
            exit_code = 1
            stdout = ""
        
        execution_result = ExecutionResult(
            task_id=task_id,
            status=final_status,
            started_at=str(context.started_at),
            finished_at=str(finished_at),
            duration=duration,
            stdout=stdout,
            stderr=safe_stderr,
            exit_code=exit_code,
            message=safe_message
        )
        
        # ─── 最终状态转换（必须成功）────────────────────
        
        transitioned = self.task_repository.transition_status(
            task_id, "running", final_status
        )
        if not transitioned:
            raise TaskStateTransitionError(task_id, "running", final_status)
        
        return execution_result
