"""
WorkOps Execution Result Collector — 执行结果收集器
Sprint032: Safe Executor Runtime

收集执行结果。不解析命令输出。
"""

from .executor_result import ExecutorResult
from .errors import ExecutorRuntimeError


class ExecutionResultCollector:
    """
    执行结果收集器。

    收集和存储执行结果。不解析命令输出。
    """

    def __init__(self):
        self._results: dict[str, ExecutorResult] = {}

    def collect_result(self, execution_id: str, result: ExecutorResult) -> None:
        """
        收集执行结果。

        Args:
            execution_id: 执行 ID
            result: 执行结果
        """
        if not isinstance(execution_id, str) or not execution_id.strip():
            raise ExecutorRuntimeError("execution_id must be a non-empty string")
        if not isinstance(result, ExecutorResult):
            raise TypeError("result must be an ExecutorResult")
        self._results[execution_id] = result

    def get_result(self, execution_id: str) -> ExecutorResult:
        """
        获取执行结果。

        Args:
            execution_id: 执行 ID

        Returns:
            ExecutorResult

        Raises:
            ExecutorRuntimeError: 结果不存在
        """
        result = self._results.get(execution_id)
        if result is None:
            raise ExecutorRuntimeError(f"Result not found: {execution_id}")
        return result

    def has_result(self, execution_id: str) -> bool:
        """检查是否有结果。"""
        return execution_id in self._results

    def list_results(self) -> list[str]:
        """返回所有已收集的执行 ID。"""
        return list(self._results.keys())

    def clear(self) -> None:
        """清空所有结果。"""
        self._results.clear()
