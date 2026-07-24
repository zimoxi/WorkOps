"""
WorkOps SSH Execution Request — SSH 执行请求
Sprint058: Linux SSH Runtime Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidSSHSessionError


@dataclass(frozen=True, slots=True)
class SSHExecutionRequest:
    """
    SSH 执行请求。不可变。

    只允许预定义的只读操作标识符。
    """

    session_id: str
    operation: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise InvalidSSHSessionError("session_id must be a non-empty string")
        if not isinstance(self.operation, str) or not self.operation.strip():
            raise InvalidSSHSessionError("operation must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))


def validate_ssh_request(request: SSHExecutionRequest) -> None:
    """
    验证 SSH 执行请求。

    Args:
        request: SSH 执行请求

    Raises:
        InvalidSSHSessionError: 验证失败
    """
    if not isinstance(request, SSHExecutionRequest):
        raise InvalidSSHSessionError("request must be an SSHExecutionRequest instance")
