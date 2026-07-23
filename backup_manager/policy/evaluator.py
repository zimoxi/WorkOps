"""
WorkOps Policy Evaluator Contract — 策略评估器接口
Sprint044: Policy Engine Foundation

只定义接口。不实现真实评估。
"""

from abc import ABC, abstractmethod

from .request import PolicyEvaluationRequest
from .result import PolicyEvaluationResult
from .model import Policy


class PolicyEvaluator(ABC):
    """
    策略评估器接口。

    只定义接口。不实现真实评估。
    """

    @abstractmethod
    def evaluate(
        self,
        request: PolicyEvaluationRequest,
        policy: Policy,
    ) -> PolicyEvaluationResult:
        """
        评估策略。

        Args:
            request: 评估请求
            policy: 策略

        Returns:
            PolicyEvaluationResult
        """
        ...
