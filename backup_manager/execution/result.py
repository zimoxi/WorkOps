"""
WorkOps ExecutionResult — 执行结果
Sprint018: Execution Engine Foundation

字段仅允许：
- task_id
- status
- started_at
- finished_at
- duration
- stdout
- stderr
- exit_code
- message

不得新增字段。
"""


class ExecutionResult:
    """执行结果"""

    def __init__(self, task_id, status, started_at, finished_at,
                 duration, stdout, stderr, exit_code, message):
        self.task_id = task_id
        self.status = status
        self.started_at = started_at
        self.finished_at = finished_at
        self.duration = duration
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.message = message

    def to_dict(self):
        return {
            "task_id": self.task_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration": self.duration,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "message": self.message,
        }
