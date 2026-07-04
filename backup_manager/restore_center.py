from __future__ import annotations

import json
from pathlib import Path, PurePosixPath


class RestoreStore:
    def __init__(self, path: Path):
        self.path = path

    def list_tasks(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_task(self, payload: dict) -> None:
        tasks = self.list_tasks()
        tasks = [task for task in tasks if task.get("id") != payload.get("id")]
        tasks.append(payload)
        tasks.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def find_task_by_staging_path(self, staging_path: str) -> dict | None:
        for task in self.list_tasks():
            if task.get("staging_path") == staging_path:
                return task
        return None


def summarize_staging_entries(root_path: str, folder_entries: list[dict]) -> list[dict]:
    if not root_path:
        return []
    root = root_path.rstrip("/")
    prefix = root + "/"
    return [
        {
            "name": item["name"],
            "path": item["path"],
            "has_files": bool(item.get("has_files", True)),
        }
        for item in folder_entries
        if item.get("path", "") == root or item.get("path", "").startswith(prefix)
    ]


def classify_staging_directories(tasks: list[dict], entries: list[dict]) -> dict[str, list[dict]]:
    entries_by_path = {entry.get("path", ""): entry for entry in entries}
    app_managed: list[dict] = []
    external: list[dict] = []

    for task in tasks:
        path = task.get("staging_path", "")
        entry = entries_by_path.get(path)
        record = {
            "name": task.get("staging_name", "")
            or PurePosixPath(path).name
            or path,
            "path": path,
            "exists": bool(entry),
            "has_files": bool(entry.get("has_files")) if entry else False,
            "task_id": task.get("id", "") if task else "",
            "snapshot_id": task.get("snapshot_id", "") if task else "",
            "created_at": task.get("created_at", "") if task else "",
            "status": task.get("status", "discovered_unverified")
            if task
            else "discovered_unverified",
            "origin": "app_managed",
        }
        app_managed.append(record)

    known_paths = {task.get("staging_path", "") for task in tasks}
    for entry in entries:
        path = entry.get("path", "")
        if path in known_paths:
            continue
        record = {
            "name": entry.get("name", ""),
            "path": path,
            "exists": True,
            "has_files": bool(entry.get("has_files")),
            "task_id": "",
            "snapshot_id": "",
            "created_at": "",
            "status": "discovered_unverified",
            "origin": "externally_discovered",
        }
        external.append(record)

    return {"app_managed": app_managed, "external": external}


def validate_staging_delete_path(root_path: str, candidate_path: str) -> str:
    root = PurePosixPath(root_path)
    candidate = PurePosixPath(candidate_path)
    if candidate == root:
        raise ValueError("restore root itself cannot be deleted")
    if not str(candidate).startswith(str(root).rstrip("/") + "/"):
        raise ValueError("staging delete path escapes the restore root")
    return str(candidate)
