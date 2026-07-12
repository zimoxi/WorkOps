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
from .errors import TaskNotFoundError, InvalidTaskStateError
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
        
        # 4. pending → running
        transitioned = self.task_repository.transition_status(
            task_id, "pending", "running"
        )
        if not transitioned:
            raise InvalidTaskStateError(task_id, task.get("status"))
        
        # ─── 执行阶段（异常返回失败 ExecutionResult）──────
        
        # 5. 创建 ExecutionContext（临时，不持久化）
        context = ExecutionContext(
            task_id=task_id,
            adapter_type="mock",
            device={"id": "mock-device", "name": task.get("device_name", "Mock Device")},
            command=f"mock-execute:{task_id}",
            started_at=datetime.now()
        )
        
        # 6. 创建 MockAdapter
        adapter = self.adapter_factory.create("mock")
        
        connected = False
        execution_result = None
        
        try:
            # 7. connect()
            adapter.connect(context.device)
            connected = True
            
            # 8. execute()
            result = adapter.execute(context.command)
            
            finished_at = datetime.now()
            duration = str(finished_at - context.started_at)
            
            # 9. 生成 ExecutionResult
            execution_result = ExecutionResult(
                task_id=task_id,
                status="success" if result.get("success") else "failed",
                started_at=str(context.started_at),
                finished_at=str(finished_at),
                duration=duration,
                stdout=result.get("stdout", ""),
                stderr=result.get("stderr", ""),
                exit_code=result.get("exit_code", 0),
                message="Execution completed"
            )
            
            # 10. running → success
            self.task_repository.transition_status(task_id, "running", execution_result.status)
            
            return execution_result
            
        except Exception as e:
            finished_at = datetime.now()
            duration = str(finished_at - context.started_at)
            
            # 安全异常映射（不泄漏原始异常信息）
            safe_message = f"Execution failed: {type(e).__name__}"
            safe_stderr = f"Error type: {type(e).__name__}"
            
            execution_result = ExecutionResult(
                task_id=task_id,
                status="failed",
                started_at=str(context.started_at),
                finished_at=str(finished_at),
                duration=duration,
                stdout="",
                stderr=safe_stderr,
                exit_code=1,
                message=safe_message
            )
            
            # running → failed
            try:
                self.task_repository.transition_status(task_id, "running", "failed")
            except:
                pass  # 状态转换失败不覆盖主错误
            
            return execution_result
            
        finally:
            # 11. disconnect
            if connected:
                try:
                    adapter.disconnect()
                except Exception as disconnect_error:
                    # disconnect 失败
                    if execution_result and execution_result.status == "success":
                        # 主执行成功 + disconnect 失败 → 整体失败
                        execution_result.status = "failed"
                        execution_result.message = "Execution succeeded but disconnect failed"
                        try:
                            self.task_repository.transition_status(task_id, "success", "failed")
                        except:
                            pass
                    else:
                        # 主执行失败 + disconnect 失败 → 保留主错误
                        pass
