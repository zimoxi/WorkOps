"""
WorkOps ExecutionContext — 执行上下文
Sprint018: Execution Engine Foundation

临时执行上下文，不持久化。

字段仅允许：
- task_id
- adapter_type（固定为 "mock"）
- device（非敏感 Mock 信息）
- command（固定 Mock 内容）
- started_at

不得包含敏感信息。
不得写回 Task。
不得持久化。
"""


class ExecutionContext:
    """执行上下文（临时，不持久化）"""

    def __init__(self, task_id, adapter_type, device, command, started_at):
        self.task_id = task_id
        self.adapter_type = adapter_type  # 固定为 "mock"
        self.device = device              # 非敏感 Mock 信息
        self.command = command            # 固定 Mock 内容
        self.started_at = started_at      # 开始时间
