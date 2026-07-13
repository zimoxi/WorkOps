"""
WorkOps Execution Errors — 执行异常定义
Sprint018: Execution Engine Foundation

前置错误（直接抛出，不修改 Task 状态）：
- TaskNotFoundError
- InvalidTaskStateError
- TaskStateTransitionError

执行错误（返回失败 ExecutionResult，Task 更新为 failed）：
- AdapterNotConnectedError
- AdapterExecutionError
- AdapterNotImplementedError
- ExecutionError
"""


class ExecutionError(Exception):
    """执行错误基类"""
    pass


class TaskNotFoundError(ExecutionError):
    """Task 不存在（前置错误）"""
    def __init__(self, task_id):
        super().__init__(f"Task not found: {task_id}")
        self.task_id = task_id


class InvalidTaskStateError(ExecutionError):
    """Task 状态无效（前置错误）"""
    def __init__(self, task_id, current_status):
        super().__init__(f"Task {task_id} has invalid status: {current_status}")
        self.task_id = task_id
        self.current_status = current_status


class TaskStateTransitionError(ExecutionError):
    """Task 状态转换失败（前置/最终错误）"""
    def __init__(self, task_id, expected_status, new_status):
        super().__init__(f"Failed to transition task {task_id}: {expected_status} -> {new_status}")
        self.task_id = task_id
        self.expected_status = expected_status
        self.new_status = new_status
