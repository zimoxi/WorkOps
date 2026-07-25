"""
WorkOps Build Metadata — 构建元数据模型
Sprint065: Release Candidate Foundation

frozen dataclass。
"""

from dataclasses import dataclass
from datetime import datetime, timezone

from .version import ReleaseVersion
from .errors import InvalidReleaseMetadataError


@dataclass(frozen=True, slots=True)
class BuildMetadata:
    """
    构建元数据。不可变。
    """

    version: ReleaseVersion
    build_id: str
    created_at: datetime = None

    def __post_init__(self):
        if not isinstance(self.version, ReleaseVersion):
            raise InvalidReleaseMetadataError("version must be a ReleaseVersion instance")
        if not isinstance(self.build_id, str) or not self.build_id.strip():
            raise InvalidReleaseMetadataError("build_id must be a non-empty string")
        if self.created_at is None:
            object.__setattr__(self, "created_at", datetime.now(timezone.utc))
