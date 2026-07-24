"""
WorkOps Health Runtime Pipeline — 健康运行时管道
Sprint055: Health Runtime Integration Foundation

只定义接口。不实现真实执行。
"""

from abc import ABC, abstractmethod

from .request import HealthExecutionRequest
from .result import HealthExecutionResult
from .errors import InvalidHealthExecutionRequestError


class HealthRuntimePipeline(ABC):
    """
    健康运行时管道接口。

    协调：Health Request → Execution Context → Runtime Connector → Health Result

    只定义接口。不实现真实执行。
    """

    @abstractmethod
    def prepare(self, request: HealthExecutionRequest) -> None:
        """
        准备健康执行。

        Args:
            request: 健康执行请求
        """
        ...

    @abstractmethod
    def execute(self, request: HealthExecutionRequest) -> HealthExecutionResult:
        """
        执行健康检查。

        Args:
            request: 健康执行请求

        Returns:
            HealthExecutionResult
        """
        ...


def validate_health_execution_request(request: HealthExecutionRequest) -> None:
    """
    验证健康执行请求。

    Args:
        request: 健康执行请求

    Raises:
        InvalidHealthExecutionRequestError: 验证失败
    """
    if not isinstance(request, HealthExecutionRequest):
        raise InvalidHealthExecutionRequestError("request must be a HealthExecutionRequest instance")
