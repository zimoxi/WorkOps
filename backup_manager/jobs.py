from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
import json
from pathlib import Path


@dataclass
class JobRecord:
    id: str
    operation_id: str
    title: str
    started_at: str
    finished_at: str
    status: str
    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    step_id: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class JobStore:
    def __init__(self, path: Path):
        self.path = path

    def append(self, record: JobRecord) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def latest(self, limit: int = 20) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        records = [json.loads(line) for line in lines[-limit:] if line.strip()]
        return list(reversed(records))


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")
