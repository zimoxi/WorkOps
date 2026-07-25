"""
WorkOps Capability Report — 能力报告模型
Sprint065: Release Candidate Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .errors import InvalidReleaseMetadataError


@dataclass(frozen=True, slots=True)
class CapabilityReport:
    """
    能力报告。不可变。
    """

    platform_name: str
    capabilities: tuple  # tuple[str, ...]
    generated_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.platform_name, str) or not self.platform_name.strip():
            raise InvalidReleaseMetadataError("platform_name must be a non-empty string")
        if not isinstance(self.capabilities, tuple) or len(self.capabilities) == 0:
            raise InvalidReleaseMetadataError("capabilities must be a non-empty tuple")
        for cap in self.capabilities:
            if not isinstance(cap, str) or not cap.strip():
                raise InvalidReleaseMetadataError("All capabilities must be non-empty strings")
        if self.generated_at is None:
            object.__setattr__(self, "generated_at", datetime.now(timezone.utc))
