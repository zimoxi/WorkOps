"""
WorkOps Adapter Descriptor — Adapter 描述符
Sprint023: Adapter Runtime Integration Foundation

frozen dataclass，描述一个 Adapter 类型的能力和属性。
"""

from dataclasses import dataclass

from .capabilities import AdapterCapability
from .errors import AdapterDescriptorError


@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    """Adapter 描述符。不可变。"""

    adapter_type: str
    capabilities: frozenset
    readonly: bool

    def __post_init__(self):
        if not isinstance(self.adapter_type, str) or not self.adapter_type.strip():
            raise AdapterDescriptorError("adapter_type must be a non-empty string")
        if not isinstance(self.capabilities, frozenset) or not self.capabilities:
            raise AdapterDescriptorError("capabilities must be a non-empty frozenset")
        if not isinstance(self.readonly, bool):
            raise AdapterDescriptorError("readonly must be a bool")
        if not self.readonly:
            raise AdapterDescriptorError("readonly must be True")
        for cap in self.capabilities:
            if not isinstance(cap, AdapterCapability):
                raise AdapterDescriptorError(
                    "All capabilities must be AdapterCapability instances"
                )
