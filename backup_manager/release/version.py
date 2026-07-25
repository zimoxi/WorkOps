"""
WorkOps Release Version — 发布版本模型
Sprint065: Release Candidate Foundation

frozen dataclass。
"""

from dataclasses import dataclass

from .errors import InvalidReleaseMetadataError


@dataclass(frozen=True, slots=True)
class ReleaseVersion:
    """
    发布版本。不可变。
    """

    major: int
    minor: int
    patch: int
    stage: str

    def __post_init__(self):
        if not isinstance(self.major, int) or self.major < 0:
            raise InvalidReleaseMetadataError("major must be a non-negative integer")
        if not isinstance(self.minor, int) or self.minor < 0:
            raise InvalidReleaseMetadataError("minor must be a non-negative integer")
        if not isinstance(self.patch, int) or self.patch < 0:
            raise InvalidReleaseMetadataError("patch must be a non-negative integer")
        if not isinstance(self.stage, str) or not self.stage.strip():
            raise InvalidReleaseMetadataError("stage must be a non-empty string")

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}-{self.stage}"
