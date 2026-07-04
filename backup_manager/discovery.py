from __future__ import annotations

from pathlib import Path
import os
import platform
import re


UNSAFE_STORAGE_MOUNTPOINTS = {
    "/",
    "/boot",
    "/etc",
    "/root",
    "/tmp",
    "/usr",
    "/var",
}


def parse_zpool_list(output: str) -> list[dict[str, str]]:
    pools: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 5:
            parts = line.split()
        if len(parts) >= 5:
            pools.append(
                {
                    "name": parts[0],
                    "size": parts[1],
                    "allocated": parts[2],
                    "free": parts[3],
                    "health": parts[4],
                }
            )
    return pools


def parse_zfs_list(output: str) -> list[dict[str, str]]:
    datasets: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            parts = line.split()
        if len(parts) >= 4:
            datasets.append(
                {
                    "name": parts[0],
                    "mountpoint": parts[1],
                    "used": parts[2],
                    "avail": parts[3],
                }
            )
    return datasets


def parse_df(output: str) -> list[dict[str, str]]:
    mounts: list[dict[str, str]] = []
    for index, line in enumerate(output.splitlines()):
        if index == 0 or not line.strip():
            continue
        parts = line.split()
        if len(parts) >= 6:
            mounts.append(
                {
                    "filesystem": parts[0],
                    "size": parts[1],
                    "used": parts[2],
                    "avail": parts[3],
                    "use_percent": parts[4],
                    "mountpoint": " ".join(parts[5:]),
                }
            )
    return mounts


def parse_remote_folders(output: str) -> list[dict[str, str]]:
    folders: list[dict[str, str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        name, separator, path = line.partition("\t")
        if separator and name and path:
            folders.append({"name": name, "path": path})
    return folders


def parse_systemd_timers(output: str) -> list[dict[str, str]]:
    timers: list[dict[str, str]] = []
    for line in output.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = re.split(r"\s{2,}", line)
        if len(parts) < 4:
            continue
        timers.append(
            {
                "id": parts[0],
                "type": "systemd",
                "next_run": parts[1],
                "last_run": parts[2],
                "command": parts[-1],
            }
        )
    return timers


def parse_crontab_lines(output: str) -> list[dict[str, str]]:
    schedules: list[dict[str, str]] = []
    for index, line in enumerate(output.splitlines(), start=1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        schedules.append(
            {
                "id": f"cron-{index}",
                "type": "cron",
                "command": stripped,
            }
        )
    return schedules


def suggest_storage_targets(
    datasets: list[dict[str, str]],
) -> list[dict[str, str]]:
    candidates: list[dict[str, str]] = []
    seen_mountpoints: set[str] = set()

    for dataset in datasets:
        name = dataset.get("name", "").strip()
        mountpoint = dataset.get("mountpoint", "").strip()
        if not name or not is_safe_storage_mountpoint(mountpoint):
            continue
        if mountpoint in seen_mountpoints:
            continue

        seen_mountpoints.add(mountpoint)
        identifier = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-")
        candidates.append(
            {
                "id": f"discovered-{identifier}",
                "name": name,
                "kind": "zfs",
                "pool_name": name.split("/", 1)[0],
                "mountpoint": mountpoint,
                "notes": "Automatically discovered. Confirm before saving.",
            }
        )

    return candidates


def suggest_restore_root_candidates(
    datasets: list[dict[str, str]],
) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    seen_paths: set[str] = set()
    for dataset in datasets:
        mountpoint = dataset.get("mountpoint", "").strip()
        name = dataset.get("name", "").strip()
        if not name or not is_safe_storage_mountpoint(mountpoint):
            continue
        path = f"{mountpoint.rstrip('/')}/.backup-manager/restore"
        if path in seen_paths:
            continue
        seen_paths.add(path)
        identifier = re.sub(r"[^A-Za-z0-9_.-]+", "-", name).strip("-")
        candidates.append(
            {
                "id": f"restore-root-{identifier}",
                "label": f"{name} restore root",
                "path": path,
                "kind": "zfs_dataset",
                "app_managed": True,
            }
        )
    return candidates


def is_safe_storage_mountpoint(mountpoint: str) -> bool:
    normalized = mountpoint.rstrip("/") or "/"
    if not mountpoint.startswith("/"):
        return False
    if normalized in UNSAFE_STORAGE_MOUNTPOINTS:
        return False
    return True


def list_first_level_folders(mountpoint: str) -> list[dict[str, str]]:
    root = Path(mountpoint)
    if not root.exists() or not root.is_dir():
        return []
    folders: list[dict[str, str]] = []
    for child in sorted(root.iterdir(), key=lambda item: item.name.casefold()):
        if child.is_dir():
            folders.append({"name": child.name, "path": str(child)})
    return folders


def local_windows_drives() -> list[dict[str, str]]:
    drives: list[dict[str, str]] = []
    if platform.system().lower() != "windows":
        return drives
    for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
        root = f"{letter}:\\"
        if os.path.exists(root):
            drives.append({"letter": letter, "path": root})
    return drives


def mock_storage() -> dict[str, object]:
    return {
        "pools": [
            {
                "name": "ExamplePool",
                "size": "20T",
                "allocated": "5.4T",
                "free": "12.7T",
                "health": "ONLINE",
            }
        ],
        "datasets": [
            {
                "name": "ExamplePool",
                "mountpoint": "/ExamplePool",
                "used": "5.4T",
                "avail": "12.7T",
            }
        ],
        "mounts": [
            {
                "filesystem": "ExamplePool",
                "size": "20T",
                "used": "5.4T",
                "avail": "12.7T",
                "use_percent": "30%",
                "mountpoint": "/ExamplePool",
            }
        ],
        "folders": [
            {"name": "Finance", "path": "/ExamplePool/Finance"},
            {"name": "Backup", "path": "/ExamplePool/Backup"},
            {"name": "Shared", "path": "/ExamplePool/Shared"},
            {"name": "SCAN", "path": "/ExamplePool/SCAN"},
            {"name": "Media", "path": "/ExamplePool/Media"},
        ],
        "storage_candidates": [
            {
                "id": "discovered-ExamplePool",
                "name": "ExamplePool",
                "kind": "zfs",
                "pool_name": "ExamplePool",
                "mountpoint": "/ExamplePool",
                "notes": "Automatically discovered. Confirm before saving.",
            }
        ],
        "restore_root_candidates": [
            {
                "id": "restore-root-ExamplePool",
                "label": "ExamplePool restore root",
                "path": "/ExamplePool/.backup-manager/restore",
                "kind": "zfs_dataset",
                "app_managed": True,
            }
        ],
        "restore_stage_entries": [
            {
                "name": "restore-001",
                "path": "/ExamplePool/.backup-manager/restore/restore-001",
                "has_files": True,
            },
            {
                "name": "manual-copy",
                "path": "/ExamplePool/.backup-manager/restore/manual-copy",
                "has_files": True,
            },
        ],
        "schedules": [
            {
                "id": "daily-restic-backup",
                "type": "systemd",
                "command": "/usr/local/sbin/restic-gensol-backup.sh",
            }
        ],
        "restic_snapshots": [
            {
                "id": "914ac36d8d507d9d",
                "short_id": "914ac36d",
                "time": "2026-06-17T15:06:37+08:00",
                "hostname": "example-nas",
                "tags": ["important"],
                "paths": [
                    "/ExamplePool/Finance",
                    "/ExamplePool/Shared",
                    "/ExamplePool/SCAN",
                ],
            },
            {
                "id": "5d43e2fa0f6d8d4c",
                "short_id": "5d43e2fa",
                "time": "2026-06-18T10:28:00+08:00",
                "hostname": "example-nas",
                "tags": ["important"],
                "paths": [
                    "/ExamplePool/Finance",
                    "/ExamplePool/Shared",
                    "/ExamplePool/SCAN",
                ],
            },
        ],
        "pbs_backups": [
            {
                "id": "vm-105-2026-06-18T01:00:00Z",
                "kind": "pbs",
                "time": "2026-06-18T01:00:00Z",
                "guest_id": "105",
                "storage": "pbs-store",
                "status": "ok",
            }
        ],
        "windows_drives": [
            {"letter": "D", "path": "D:\\"},
            {"letter": "E", "path": "E:\\"},
        ],
    }
