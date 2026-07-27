"""
WorkOps Release Checklist — 发布检查清单
Sprint074: WorkOps v1.0 Stable Release

ReleaseChecklistItem, ReleaseChecklist
"""

from dataclasses import dataclass
from .errors import InvalidReleaseMetadataError


@dataclass(frozen=True, slots=True)
class ReleaseChecklistItem:
    """
    发布检查项。不可变。
    """

    name: str
    completed: bool

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise InvalidReleaseMetadataError("name must be a non-empty string")
        if not isinstance(self.completed, bool):
            raise InvalidReleaseMetadataError("completed must be a bool")


@dataclass(frozen=True, slots=True)
class ReleaseChecklist:
    """
    发布检查清单。不可变。
    """

    items: tuple  # tuple[ReleaseChecklistItem, ...]

    def __post_init__(self):
        if not isinstance(self.items, tuple) or len(self.items) == 0:
            raise InvalidReleaseMetadataError("items must be a non-empty tuple")
        for item in self.items:
            if not isinstance(item, ReleaseChecklistItem):
                raise InvalidReleaseMetadataError("All items must be ReleaseChecklistItem instances")

    @property
    def all_completed(self) -> bool:
        """是否所有项都已完成。"""
        return all(item.completed for item in self.items)

    @property
    def completed_count(self) -> int:
        """已完成项数。"""
        return sum(1 for item in self.items if item.completed)

    @property
    def total_count(self) -> int:
        """总项数。"""
        return len(self.items)
