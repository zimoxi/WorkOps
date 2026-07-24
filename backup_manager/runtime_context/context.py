"""
WorkOps Execution Context — 执行上下文
Sprint051: Adapter Execution Context Foundation

frozen dataclass + AdapterRuntimeContext ABC。
"""

from dataclasses import dataclass
from abc import ABC, abstractmethod

from .model import ExecutionMode
from .metadata import ExecutionMetadata
from .errors import InvalidExecutionContextError

# CredentialReference is in credentials domain
from ..credentials.binding_model import CredentialReference


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    """
    执行上下文。不可变。

    包含执行元数据、模式、凭证引用。
    不包含凭证值。
    """

    metadata: ExecutionMetadata
    mode: ExecutionMode
    credential_reference: CredentialReference | None = None

    def __post_init__(self):
        if not isinstance(self.metadata, ExecutionMetadata):
            raise InvalidExecutionContextError("metadata must be an ExecutionMetadata instance")
        if not isinstance(self.mode, ExecutionMode):
            raise InvalidExecutionContextError("mode must be an ExecutionMode instance")
        if self.credential_reference is not None:
            if not isinstance(self.credential_reference, CredentialReference):
                raise InvalidExecutionContextError("credential_reference must be a CredentialReference or None")


class AdapterRuntimeContext(ABC):
    """
    适配器运行时上下文接口。

    只定义接口。不实现真实执行。
    """

    @abstractmethod
    def create(
        self,
        metadata: ExecutionMetadata,
        mode: ExecutionMode,
        credential_reference: CredentialReference | None,
    ) -> ExecutionContext:
        """
        创建执行上下文。

        Args:
            metadata: 执行元数据
            mode: 执行模式
            credential_reference: 凭证引用

        Returns:
            ExecutionContext
        """
        ...


def validate_execution_context(context: ExecutionContext) -> None:
    """
    验证执行上下文。

    Args:
        context: 执行上下文

    Raises:
        InvalidExecutionContextError: 验证失败
    """
    if not isinstance(context, ExecutionContext):
        raise InvalidExecutionContextError("context must be an ExecutionContext instance")
    # metadata 已在其 __post_init__ 中验证
    # mode 已在 ExecutionContext.__post_init__ 中验证
    # credential_reference 已在 ExecutionContext.__post_init__ 中验证
