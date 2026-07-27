"""
Backward-compatible aliases for legacy server.py (pre-Sprint039 API).

server.py imports JobRecord, JobStore, now_iso from .jobs.
Sprint039 replaced the old module with new domain models.
This file provides shim classes so server.py can still import.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone


def now_iso() -> str:
    """Return current UTC time as ISO string."""
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    """Legacy job record used by server.py."""
    id: str = ""
    operation_id: str = ""
    title: str = ""
    started_at: str = ""
    finished_at: str = ""
    status: str = ""
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    command: str = ""


class JobStore:
    """Legacy file-backed job store used by server.py."""

    def __init__(self, path):
        self._path = path
        self._records: list[JobRecord] = []

    def append(self, record: JobRecord) -> None:
        self._records.append(record)

    def latest(self, limit: int = 50) -> list[dict]:
        items = self._records[-limit:]
        from dataclasses import asdict
        return [asdict(r) for r in reversed(items)]
