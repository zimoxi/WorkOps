# Host-Aware Backup Control Center Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evolve Backup Manager into a host-aware backup and restore control center that can identify OMV, PVE, generic Linux, and the current local Windows machine, discover existing backup state, and manage restore staging safely.

**Architecture:** Keep the current lightweight Python HTTP server and vanilla-JS frontend, but add three focused backend modules: one for platform and capability detection, one for normalized inventory aggregation, and one for restore-center state and staging-directory management. Extend the workflow and UI to consume those new structures instead of treating every host as OMV-like.

**Tech Stack:** Python 3.11/3.12 standard library, Paramiko, vanilla JavaScript, CSS, `unittest`, existing HTTP server and JSON file stores.

---

This spec spans several independent subsystems. This plan keeps them in one document for handoff convenience, but it sequences them into five working slices so every task yields testable software instead of a half-wired mega-branch.

This directory is not a Git repository. Under `CODEX_GUARD.md`, implementation may write code but must not automatically run commands, tests, SSH, Docker, backup, restore, migration, or network operations. Every command below is a manual verification instruction for the operator.

## File Map

- Create `backup_manager/profile.py`: detect platform kind and backup-related capabilities from local context or remote command availability.
- Create `backup_manager/inventory.py`: normalize discovered pools, repositories, schedules, backup artifacts, restore tasks, and warnings into one payload.
- Create `backup_manager/restore_center.py`: persist restore task records, classify staging directories, and validate delete boundaries.
- Modify `backup_manager/config.py`: persist restore-root selection, optional platform override, and restore-related settings.
- Modify `backup_manager/discovery.py`: add restore-root candidate helpers and keep storage-discovery helpers generic.
- Modify `backup_manager/commands.py`: add guarded operations for restore-root preparation and staging-directory deletion.
- Modify `backup_manager/jobs.py`: store workflow step IDs and structured metadata so restore and inventory records can link to jobs.
- Modify `backup_manager/workflow.py`: replace the current 10-step OMV-biased workflow with the 11-step host-aware flow and `unavailable` states.
- Modify `backup_manager/server.py`: return `profile`, `capabilities`, `inventory`, and restore-center data from state and discovery endpoints; add restore-center endpoints.
- Modify `static/app.js`: render host profile, inventory lists, restore center, restore staging status, and host-aware next-step guidance.
- Modify `static/workflow.js`: support the new step IDs, `unavailable` state, and restore-center copy.
- Modify `static/styles.css`: add inventory list, restore-center table, badge, and dialog styles.
- Create `tests/test_profile.py`: pure platform and capability detection tests.
- Create `tests/test_inventory.py`: normalized inventory tests.
- Create `tests/test_restore_center.py`: restore-task and staging-directory tests.
- Modify `tests/test_workflow.py`: host-aware workflow state tests.
- Modify `tests/test_http_api.py`: profile, inventory, and restore-center endpoint tests.
- Modify `tests/test_discovery.py`: restore-root candidate and safety-filter tests.
- Modify `README.md`: document supported hosts, restore staging rules, and manual verification instructions.

### Task 1: Persist Host-Aware Restore State

**Files:**
- Modify: `backup_manager/config.py`
- Modify: `backup_manager/jobs.py`
- Create: `backup_manager/restore_center.py`
- Create: `tests/test_restore_center.py`

- [ ] **Step 1: Write failing persistence tests**

Create `tests/test_restore_center.py`:

```python
import tempfile
import unittest
from pathlib import Path

from backup_manager.config import AppConfig
from backup_manager.restore_center import RestoreStore, classify_staging_directories


class RestoreCenterTests(unittest.TestCase):
    def test_config_round_trips_restore_root_selection(self):
        config = AppConfig.from_dict(
            {
                "restore_roots": [
                    {
                        "id": "root-1",
                        "label": "Primary Restore Root",
                        "path": "/tank/.backup-manager/restore",
                        "kind": "zfs_dataset",
                        "app_managed": True,
                    }
                ],
                "active_restore_root_id": "root-1",
            }
        )

        restored = AppConfig.from_json(config.to_json())

        self.assertEqual(restored.active_restore_root_id, "root-1")
        self.assertEqual(restored.restore_roots[0].path, "/tank/.backup-manager/restore")

    def test_restore_store_persists_restore_task_records(self):
        with tempfile.TemporaryDirectory() as temp:
            store = RestoreStore(Path(temp) / "restore_tasks.json")
            store.save_task(
                {
                    "id": "restore-001",
                    "snapshot_id": "914ac36d",
                    "selected_paths": ["/Gensol/SCAN"],
                    "staging_name": "restore-001",
                    "staging_path": "/Gensol/.backup-manager/restore/restore-001",
                    "status": "restored_pending_review",
                    "origin": "app_managed",
                    "created_at": "2026-06-23T12:00:00",
                }
            )

            tasks = store.list_tasks()

            self.assertEqual(tasks[0]["id"], "restore-001")
            self.assertEqual(tasks[0]["status"], "restored_pending_review")

    def test_classify_staging_directories_marks_external_entries(self):
        tasks = [
            {
                "id": "restore-001",
                "staging_name": "restore-001",
                "staging_path": "/tank/.backup-manager/restore/restore-001",
                "status": "cleanup_pending",
                "snapshot_id": "914ac36d",
                "created_at": "2026-06-23T12:00:00",
            }
        ]
        entries = [
            {"name": "restore-001", "path": "/tank/.backup-manager/restore/restore-001", "has_files": True},
            {"name": "manual-copy", "path": "/tank/.backup-manager/restore/manual-copy", "has_files": True},
        ]

        result = classify_staging_directories(tasks, entries)

        self.assertEqual(result["app_managed"][0]["status"], "cleanup_pending")
        self.assertEqual(result["external"][0]["name"], "manual-copy")
```

- [ ] **Step 2: Manually run the new tests and confirm RED**

```powershell
py -m unittest tests.test_restore_center -v
```

Expected: `ImportError` because `backup_manager.restore_center` does not exist and `AppConfig` does not yet persist restore-root objects.

- [ ] **Step 3: Add restore-root configuration and structured job metadata**

Modify `backup_manager/config.py` to add:

```python
@dataclass
class RestoreRoot:
    id: str
    label: str
    path: str
    kind: str = "directory"
    app_managed: bool = False


@dataclass
class AppConfig:
    active_restore_root_id: str = ""
    restore_roots: list[RestoreRoot] = field(default_factory=list)
    platform_override: str = ""
    notification_emails: list[str] = field(default_factory=list)
    notification_sender: str = ""
```

Also update `from_dict()`:

```python
restore_roots=[
    RestoreRoot(**item) for item in data.get("restore_roots", [])
],
active_restore_root_id=data.get("active_restore_root_id", ""),
platform_override=data.get("platform_override", ""),
notification_emails=list(data.get("notification_emails", [])),
notification_sender=data.get("notification_sender", ""),
```

Modify `backup_manager/jobs.py` to extend `JobRecord`:

```python
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
    metadata: dict[str, object] | None = None
```

- [ ] **Step 4: Implement the restore task store and staging classifier**

Create `backup_manager/restore_center.py`:

```python
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import PurePosixPath, Path


@dataclass
class RestoreTaskRecord:
    id: str
    snapshot_id: str
    selected_paths: list[str]
    staging_name: str
    staging_path: str
    status: str
    origin: str
    created_at: str
    target_path: str = ""


class RestoreStore:
    def __init__(self, path: Path):
        self.path = path

    def list_tasks(self) -> list[dict]:
        if not self.path.exists():
            return []
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save_task(self, payload: dict) -> None:
        tasks = self.list_tasks()
        tasks = [task for task in tasks if task["id"] != payload["id"]]
        tasks.append(payload)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding="utf-8")


def classify_staging_directories(tasks: list[dict], entries: list[dict]) -> dict[str, list[dict]]:
    known = {task["staging_path"]: task for task in tasks}
    app_managed: list[dict] = []
    external: list[dict] = []
    for entry in entries:
        task = known.get(entry["path"])
        record = {
            "name": entry["name"],
            "path": entry["path"],
            "has_files": bool(entry.get("has_files")),
            "task_id": task["id"] if task else "",
            "snapshot_id": task["snapshot_id"] if task else "",
            "created_at": task["created_at"] if task else "",
            "status": task["status"] if task else "discovered_unverified",
            "origin": "app_managed" if task else "externally_discovered",
        }
        (app_managed if task else external).append(record)
    return {"app_managed": app_managed, "external": external}


def validate_staging_delete_path(root_path: str, candidate_path: str) -> str:
    root = PurePosixPath(root_path)
    candidate = PurePosixPath(candidate_path)
    if candidate == root or not str(candidate).startswith(str(root).rstrip("/") + "/"):
        raise ValueError("staging delete path escapes the restore root")
    return str(candidate)
```

- [ ] **Step 5: Manually run the tests and commit**

```powershell
py -m unittest tests.test_restore_center -v
git add backup_manager/config.py backup_manager/jobs.py backup_manager/restore_center.py tests/test_restore_center.py
git commit -m "feat: persist restore center state"
```

Expected: restore-center tests pass and the commit records config plus restore-task persistence.

### Task 2: Detect Platform And Capabilities

**Files:**
- Create: `backup_manager/profile.py`
- Create: `tests/test_profile.py`
- Modify: `backup_manager/server.py`

- [ ] **Step 1: Write failing profile-detection tests**

Create `tests/test_profile.py`:

```python
import unittest

from backup_manager.profile import (
    detect_local_platform,
    detect_remote_platform,
    detect_remote_capabilities,
)


class ProfileTests(unittest.TestCase):
    def test_local_windows_is_classified_as_windows_local(self):
        profile = detect_local_platform(system_name="Windows")
        self.assertEqual(profile["kind"], "windows-local")

    def test_remote_pve_wins_over_generic_linux(self):
        profile = detect_remote_platform(
            command_presence={"pveversion": True, "qm": True, "pct": True, "pvesm": True}
        )
        self.assertEqual(profile["kind"], "pve")

    def test_remote_omv_is_detected_when_pve_commands_are_missing(self):
        profile = detect_remote_platform(
            command_presence={"omv-confdbadm": True, "pveversion": False}
        )
        self.assertEqual(profile["kind"], "omv")

    def test_capability_detection_is_independent_of_platform(self):
        capabilities = detect_remote_capabilities(
            command_presence={
                "zpool": True,
                "zfs": True,
                "restic": False,
                "rclone": True,
                "systemctl": True,
                "crontab": False,
            }
        )
        self.assertTrue(capabilities["zfs"])
        self.assertFalse(capabilities["restic"])
        self.assertTrue(capabilities["rclone"])
        self.assertTrue(capabilities["systemd"])
```

- [ ] **Step 2: Manually run the tests and confirm RED**

```powershell
py -m unittest tests.test_profile -v
```

Expected: `ImportError` because `backup_manager.profile` does not exist.

- [ ] **Step 3: Implement pure detection helpers**

Create `backup_manager/profile.py`:

```python
from __future__ import annotations


def detect_local_platform(system_name: str | None = None) -> dict[str, object]:
    system_name = (system_name or "").lower()
    if system_name == "windows":
        return {"kind": "windows-local", "label": "Windows Local", "source": "local"}
    return {"kind": "linux", "label": "Linux", "source": "local"}


def detect_remote_platform(command_presence: dict[str, bool]) -> dict[str, object]:
    if all(command_presence.get(name, False) for name in ("pveversion", "qm", "pct", "pvesm")):
        return {"kind": "pve", "label": "Proxmox VE", "source": "remote"}
    if command_presence.get("omv-confdbadm", False):
        return {"kind": "omv", "label": "OpenMediaVault", "source": "remote"}
    return {"kind": "linux", "label": "Linux", "source": "remote"}


def detect_remote_capabilities(command_presence: dict[str, bool]) -> dict[str, bool]:
    return {
        "zfs": command_presence.get("zpool", False) and command_presence.get("zfs", False),
        "restic": command_presence.get("restic", False),
        "rclone": command_presence.get("rclone", False),
        "systemd": command_presence.get("systemctl", False),
        "cron": command_presence.get("crontab", False),
        "pbs": command_presence.get("proxmox-backup-client", False) or command_presence.get("pvesm", False),
        "smb": command_presence.get("smbstatus", False) or command_presence.get("mount.cifs", False),
    }
```

- [ ] **Step 4: Add a small server helper that probes capability commands**

Add to `backup_manager/server.py`:

```python
PROFILE_PROBE_COMMANDS = (
    "pveversion",
    "qm",
    "pct",
    "pvesm",
    "omv-confdbadm",
    "zpool",
    "zfs",
    "restic",
    "rclone",
    "systemctl",
    "crontab",
    "smbstatus",
    "mount.cifs",
    "proxmox-backup-client",
)


def probe_command_presence(command_executor) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for name in PROFILE_PROBE_COMMANDS:
        probe = command_executor.run_argv(["sh", "-lc", f"command -v {name} >/dev/null 2>&1"])
        result[name] = probe.returncode == 0
    return result
```

Use this later from discovery and `/api/state`; do not wire new API output yet in this task.

- [ ] **Step 5: Manually run the tests and commit**

```powershell
py -m unittest tests.test_profile -v
git add backup_manager/profile.py backup_manager/server.py tests/test_profile.py
git commit -m "feat: detect host platform and capabilities"
```

Expected: profile tests pass and the server contains a reusable probe helper without changing user-visible state yet.

### Task 3: Build Normalized Inventory And Restore-Center Views

**Files:**
- Create: `backup_manager/inventory.py`
- Modify: `backup_manager/discovery.py`
- Modify: `backup_manager/restore_center.py`
- Create: `tests/test_inventory.py`
- Modify: `tests/test_discovery.py`

- [ ] **Step 1: Write failing inventory and restore-root tests**

Create `tests/test_inventory.py`:

```python
import unittest

from backup_manager.inventory import build_inventory


class InventoryTests(unittest.TestCase):
    def test_inventory_includes_app_managed_and_external_staging_lists(self):
        inventory = build_inventory(
            config={
                "active_storage_id": "tank",
                "restic": {"repository": "/tank/restic"},
            },
            profile={"kind": "omv"},
            capabilities={"zfs": True, "restic": True},
            discovery={
                "pools": [{"name": "tank", "free": "8T"}],
                "datasets": [{"name": "tank", "mountpoint": "/tank", "used": "2T", "avail": "8T"}],
            },
            restore_tasks=[
                {
                    "id": "restore-001",
                    "staging_path": "/tank/.backup-manager/restore/restore-001",
                    "staging_name": "restore-001",
                    "snapshot_id": "914ac36d",
                    "status": "cleanup_pending",
                    "created_at": "2026-06-23T12:00:00",
                }
            ],
            staging_entries=[
                {"name": "restore-001", "path": "/tank/.backup-manager/restore/restore-001", "has_files": True},
                {"name": "manual-copy", "path": "/tank/.backup-manager/restore/manual-copy", "has_files": True},
            ],
            jobs=[],
        )

        self.assertEqual(inventory["restore_center"]["app_managed"][0]["task_id"], "restore-001")
        self.assertEqual(inventory["restore_center"]["external"][0]["name"], "manual-copy")
```

Append to `tests/test_discovery.py`:

```python
from backup_manager.discovery import suggest_restore_root_candidates


    def test_suggest_restore_root_candidates_prefers_safe_dataset_mounts(self):
        datasets = [
            {"name": "rpool/ROOT", "mountpoint": "/", "used": "8G", "avail": "20G"},
            {"name": "tank", "mountpoint": "/tank", "used": "2T", "avail": "8T"},
        ]

        result = suggest_restore_root_candidates(datasets)

        self.assertEqual(
            result,
            [
                {
                    "id": "restore-root-tank",
                    "label": "tank restore root",
                    "path": "/tank/.backup-manager/restore",
                    "kind": "zfs_dataset",
                    "app_managed": True,
                }
            ],
        )
```

- [ ] **Step 2: Manually run the tests and confirm RED**

```powershell
py -m unittest tests.test_inventory tests.test_discovery -v
```

Expected: `ImportError` for `backup_manager.inventory` and missing `suggest_restore_root_candidates`.

- [ ] **Step 3: Add restore-root candidate generation**

Extend `backup_manager/discovery.py` with:

```python
def suggest_restore_root_candidates(datasets: list[dict[str, str]]) -> list[dict[str, object]]:
    candidates: list[dict[str, object]] = []
    for dataset in datasets:
        mountpoint = dataset.get("mountpoint", "").strip()
        name = dataset.get("name", "").strip()
        if not name or not is_safe_storage_mountpoint(mountpoint):
            continue
        candidates.append(
            {
                "id": f"restore-root-{re.sub(r'[^A-Za-z0-9_.-]+', '-', name).strip('-')}",
                "label": f"{name} restore root",
                "path": f"{mountpoint.rstrip('/')}/.backup-manager/restore",
                "kind": "zfs_dataset",
                "app_managed": True,
            }
        )
    return candidates
```

- [ ] **Step 4: Implement inventory normalization**

Create `backup_manager/inventory.py`:

```python
from __future__ import annotations

from .restore_center import classify_staging_directories


def build_inventory(
    *,
    config: dict,
    profile: dict,
    capabilities: dict,
    discovery: dict,
    restore_tasks: list[dict],
    staging_entries: list[dict],
    jobs: list[dict],
) -> dict[str, object]:
    restore_center = classify_staging_directories(restore_tasks, staging_entries)
    return {
        "profile": profile,
        "capabilities": capabilities,
        "storage": {
            "pools": discovery.get("pools", []),
            "datasets": discovery.get("datasets", []),
            "folders": discovery.get("folders", []),
            "storage_candidates": discovery.get("storage_candidates", []),
            "restore_root_candidates": discovery.get("restore_root_candidates", []),
        },
        "backup_tasks": [],
        "backup_artifacts": [],
        "restore_tasks": restore_tasks,
        "restore_center": restore_center,
        "warnings": [],
    }
```

Also extend `backup_manager/restore_center.py` with:

```python
def summarize_staging_entries(root_path: str, folder_entries: list[dict]) -> list[dict]:
    prefix = root_path.rstrip("/") + "/"
    return [
        {
            "name": item["name"],
            "path": item["path"],
            "has_files": bool(item.get("has_files", True)),
        }
        for item in folder_entries
        if item["path"].startswith(prefix)
    ]
```

- [ ] **Step 5: Manually run the tests and commit**

```powershell
py -m unittest tests.test_inventory tests.test_discovery tests.test_restore_center -v
git add backup_manager/discovery.py backup_manager/inventory.py backup_manager/restore_center.py tests/test_inventory.py tests/test_discovery.py tests/test_restore_center.py
git commit -m "feat: normalize inventory and restore-root candidates"
```

Expected: the new inventory and restore-root tests pass and the backend can represent restore-center state without UI changes yet.

### Task 4: Wire Workflow And HTTP APIs To The New Inventory Model

**Files:**
- Modify: `backup_manager/workflow.py`
- Modify: `backup_manager/server.py`
- Modify: `backup_manager/commands.py`
- Modify: `tests/test_workflow.py`
- Modify: `tests/test_http_api.py`

- [ ] **Step 1: Write failing workflow and API tests for host-aware state**

Append to `tests/test_workflow.py` inside the existing `WorkflowTests` class:

```python
    def test_restore_root_step_is_required_before_restore_center(self):
        config = AppConfig.from_dict(
            {
                "storage_targets": [{"id": "tank", "name": "tank", "kind": "zfs", "mountpoint": "/tank", "pool_name": "tank"}],
                "active_storage_id": "tank",
            }
        )
        result = derive_workflow(config, [])
        restore_root = next(step for step in result["steps"] if step["id"] == "restore_root")
        restore_center = next(step for step in result["steps"] if step["id"] == "restore_center")
        self.assertEqual(restore_root["status"], "not_started")
        self.assertEqual(restore_center["status"], "not_started")

    def test_windows_step_can_be_unavailable_on_non_windows_runtime(self):
        result = derive_workflow(AppConfig.default(), [], runtime={"local_platform": "linux"})
        windows = next(step for step in result["steps"] if step["id"] == "windows")
        self.assertEqual(windows["status"], "unavailable")
```

Append to `tests/test_http_api.py`:

```python
    def test_state_includes_profile_inventory_and_restore_center(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/state")

        self.assertEqual(status, 200)
        self.assertIn("profile", payload)
        self.assertIn("inventory", payload)
        self.assertIn("restore_center", payload["inventory"])

    def test_restore_center_endpoint_lists_app_and_external_staging(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.restore_store.save_task(
                {
                    "id": "restore-001",
                    "snapshot_id": "914ac36d",
                    "selected_paths": ["/Gensol/SCAN"],
                    "staging_name": "restore-001",
                    "staging_path": "/tank/.backup-manager/restore/restore-001",
                    "status": "cleanup_pending",
                    "origin": "app_managed",
                    "created_at": "2026-06-23T12:00:00",
                }
            )
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/restore-center")

        self.assertEqual(status, 200)
        self.assertIn("app_managed", payload)
        self.assertIn("external", payload)
```

- [ ] **Step 2: Manually run the tests and confirm RED**

```powershell
py -m unittest tests.test_workflow tests.test_http_api -v
```

Expected: missing `restore_root` and `restore_center` step IDs, plus missing `profile`, `inventory`, and `/api/restore-center`.

- [ ] **Step 3: Update the workflow model to the new 11-step sequence**

Modify `backup_manager/workflow.py`:

```python
STEP_DEFINITIONS = (
    ("connect", "连接与识别", False),
    ("storage", "确认存储目标", False),
    ("restore_root", "恢复暂存区", False),
    ("dataset", "Dataset 迁移", True),
    ("restic", "配置 NAS / Restic", False),
    ("first_backup", "首次备份", False),
    ("restore_center", "恢复中心", False),
    ("schedule", "自动计划与通知", False),
    ("windows", "Windows 本机备份", True),
    ("cloud", "云端副本", True),
    ("pve_pbs", "PVE / PBS", True),
)


def derive_workflow(config: AppConfig, jobs: list[Any], runtime: dict[str, object] | None = None) -> dict[str, Any]:
    runtime = runtime or {}
```

Implement status rules:

```python
if step_id == "restore_root":
    configured = bool(config.restore_roots and config.active_restore_root_id)
    return ("complete", config.workflow.completed_at.get("restore_root", "")) if configured else ("not_started", "")

if step_id == "restore_center":
    finished_at = latest_success_time(jobs, "restic-restore")
    return ("complete", finished_at) if finished_at else ("not_started", "")

if step_id == "windows" and runtime.get("local_platform") != "windows":
    return "unavailable", ""
```

- [ ] **Step 4: Expose profile, inventory, and restore-center endpoints**

Modify `backup_manager/server.py`:

```python
class AppContext:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.config_store = ConfigStore(data_dir / "config.json")
        self.job_store = JobStore(data_dir / "jobs.jsonl")
        self.restore_store = RestoreStore(data_dir / "restore_tasks.json")
        self.catalog = CommandCatalog()
```

Build the state payload with:

```python
def discover_profile(config: AppConfig) -> tuple[dict[str, object], dict[str, bool]]:
    if config.executor_mode == "local":
        profile = detect_local_platform(platform.system())
        capabilities = detect_remote_capabilities({})
        return profile, capabilities
    executor = create_executor(config)
    command_presence = probe_command_presence(executor)
    return detect_remote_platform(command_presence), detect_remote_capabilities(command_presence)


def build_state_inventory(context: AppContext, config: AppConfig, discovery: dict[str, object]) -> dict[str, object]:
    profile, capabilities = discover_profile(config)
    return build_inventory(
        config=config.to_dict(),
        profile=profile,
        capabilities=capabilities,
        discovery=discovery,
        restore_tasks=context.restore_store.list_tasks(),
        staging_entries=discovery.get("restore_stage_entries", []),
        jobs=context.job_store.latest(),
    )
```

Add:

```python
config = context.config_store.load()
discovery = discover_storage(config)
inventory = build_state_inventory(context, config, discovery)
profile = inventory["profile"]
capabilities = inventory["capabilities"]
workflow = derive_workflow(
    config,
    context.job_store.latest(),
    runtime={"local_platform": "windows" if profile["kind"] == "windows-local" else "linux"},
)

if parsed.path == "/api/restore-center":
    inventory = build_state_inventory(context, config, discovery)
    self.send_json(inventory["restore_center"])
    return
```

Add a guarded delete operation to `backup_manager/commands.py`:

```python
"restore-staging-delete": self._restore_staging_delete,
```

with:

```python
def _restore_staging_delete(self, payload: dict) -> PreparedCommand:
    path = validate_restore_target(payload.get("target", ""))
    return PreparedCommand(
        id="restore-staging-delete",
        title="删除恢复暂存目录",
        argv=["rm", "-rf", path],
        env=[],
        danger="high",
        instructions="删除恢复暂存目录。只允许删除恢复根目录下面的任务目录。",
        impact="会永久删除该暂存目录中的所有文件。",
        recovery="如果误删，必须回到备份仓库重新恢复数据。",
        confirm_text=payload.get("confirm_text", ""),
    )
```

- [ ] **Step 5: Manually run the tests and commit**

```powershell
py -m unittest tests.test_workflow tests.test_http_api -v
git add backup_manager/workflow.py backup_manager/server.py backup_manager/commands.py tests/test_workflow.py tests/test_http_api.py
git commit -m "feat: expose host-aware workflow and restore-center apis"
```

Expected: workflow and API tests pass, state now includes profile plus inventory, and restore-center data is queryable.

### Task 5: Populate Backup Tasks, Artifacts, And Schedule Inventory

**Files:**
- Modify: `backup_manager/inventory.py`
- Modify: `backup_manager/discovery.py`
- Modify: `backup_manager/server.py`
- Modify: `tests/test_inventory.py`
- Modify: `tests/test_http_api.py`

- [ ] **Step 1: Write failing task-list and warning tests**

Append to `tests/test_inventory.py`:

```python
    def test_inventory_builds_backup_task_rows_from_config_and_jobs(self):
        inventory = build_inventory(
            config={
                "restic": {"repository": "/tank/restic", "password_file": "/root/.config/restic.pass"},
                "backup_sets": [{"id": "important", "name": "Important", "include_paths": ["/tank/SCAN"]}],
                "windows_backup": {"enabled": True, "source_drives": ["D:\\", "E:\\"], "smb_target": "\\\\10.0.0.10\\Backup"},
                "cloud_remote": {"enabled": True, "remote_name": "baidu:/restic", "sync_source": "/tank/restic"},
                "pve_pbs": {"enabled": True, "pve_host": "10.0.0.3", "pbs_storage": "pbs-store"},
            },
            profile={"kind": "pve"},
            capabilities={"restic": True, "rclone": True, "pbs": True},
            discovery={"pools": [], "datasets": [], "schedules": []},
            restore_tasks=[],
            staging_entries=[],
            jobs=[
                {"operation_id": "restic-backup", "status": "success", "finished_at": "2026-06-23T08:00:00"},
                {"operation_id": "cloud-rclone-sync", "status": "failed", "finished_at": "2026-06-23T09:00:00"},
            ],
        )

        self.assertEqual(inventory["backup_tasks"][0]["type"], "restic")
        self.assertEqual(inventory["backup_tasks"][0]["latest_result"], "success")
        self.assertEqual(inventory["backup_tasks"][1]["type"], "windows_local")

    def test_inventory_warns_when_duplicate_schedules_are_discovered(self):
        inventory = build_inventory(
            config={"restic": {"repository": "/tank/restic"}},
            profile={"kind": "omv"},
            capabilities={"systemd": True},
            discovery={
                "pools": [],
                "datasets": [],
                "schedules": [
                    {"id": "daily-backup-a", "type": "systemd", "command": "/usr/local/sbin/restic-gensol-backup.sh"},
                    {"id": "daily-backup-b", "type": "cron", "command": "/usr/local/sbin/restic-gensol-backup.sh"},
                ],
            },
            restore_tasks=[],
            staging_entries=[],
            jobs=[],
        )

        self.assertIn("duplicate_schedule", [item["code"] for item in inventory["warnings"]])
```

Append to `tests/test_http_api.py`:

```python
    def test_state_exposes_backup_tasks_and_warnings(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.config_store.save(
                AppConfig.from_dict(
                    {
                        "restic": {"repository": "/tank/restic", "password_file": "/root/.config/restic.pass"},
                        "backup_sets": [{"id": "important", "name": "Important", "include_paths": ["/tank/SCAN"]}],
                    }
                )
            )
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/state")

        self.assertEqual(status, 200)
        self.assertIn("backup_tasks", payload["inventory"])
        self.assertIn("warnings", payload["inventory"])
```

- [ ] **Step 2: Manually run the tests and confirm RED**

```powershell
py -m unittest tests.test_inventory tests.test_http_api -v
```

Expected: inventory task rows and warnings are missing from the current payload.

- [ ] **Step 3: Add schedule parsing helpers**

Extend `backup_manager/discovery.py`:

```python
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
        schedules.append({"id": f"cron-{index}", "type": "cron", "command": stripped})
    return schedules
```

- [ ] **Step 4: Populate backup task rows, artifact rows, and warnings**

Extend `backup_manager/inventory.py`:

```python
def build_inventory(
    *,
    config: dict,
    profile: dict,
    capabilities: dict,
    discovery: dict,
    restore_tasks: list[dict],
    staging_entries: list[dict],
    jobs: list[dict],
) -> dict[str, object]:
    restore_center = classify_staging_directories(restore_tasks, staging_entries)
    return {
        "profile": profile,
        "capabilities": capabilities,
        "storage": {
            "pools": discovery.get("pools", []),
            "datasets": discovery.get("datasets", []),
            "folders": discovery.get("folders", []),
            "storage_candidates": discovery.get("storage_candidates", []),
            "restore_root_candidates": discovery.get("restore_root_candidates", []),
        },
        "backup_tasks": summarize_backup_tasks(config, jobs),
        "backup_artifacts": summarize_backup_artifacts(discovery),
        "restore_tasks": restore_tasks,
        "restore_center": restore_center,
        "warnings": summarize_warnings(discovery.get("schedules", []), restore_center),
    }


def summarize_backup_tasks(config: dict, jobs: list[dict]) -> list[dict]:
    rows: list[dict] = []
    restic = config.get("restic", {})
    if restic.get("repository"):
        rows.append(
            {
                "name": "NAS / Restic",
                "type": "restic",
                "destination": restic["repository"],
                "latest_result": latest_job_status(jobs, "restic-backup"),
                "origin": "app_managed",
            }
        )
    windows = config.get("windows_backup", {})
    if windows.get("enabled") and windows.get("smb_target"):
        rows.append(
            {
                "name": "Windows Local Backup",
                "type": "windows_local",
                "destination": windows["smb_target"],
                "latest_result": latest_job_status(jobs, "windows-robocopy-preview"),
                "origin": "app_managed",
            }
        )
    cloud = config.get("cloud_remote", {})
    if cloud.get("enabled") and cloud.get("remote_name"):
        rows.append(
            {
                "name": "Cloud Copy",
                "type": "cloud",
                "destination": cloud["remote_name"],
                "latest_result": latest_job_status(jobs, "cloud-rclone-sync"),
                "origin": "app_managed",
            }
        )
    pve = config.get("pve_pbs", {})
    if pve.get("enabled") and pve.get("pbs_storage"):
        rows.append(
            {
                "name": "PVE / PBS",
                "type": "pve_pbs",
                "destination": pve["pbs_storage"],
                "latest_result": latest_job_status(jobs, "pve-vzdump"),
                "origin": "app_managed",
            }
        )
    return rows


def summarize_backup_artifacts(discovery: dict) -> list[dict]:
    return discovery.get("restic_snapshots", []) + discovery.get("pbs_backups", [])


def summarize_warnings(schedules: list[dict], restore_center: dict) -> list[dict]:
    warnings: list[dict] = []
    commands: dict[str, list[str]] = {}
    for item in schedules:
        command = item.get("command", "")
        if not command:
            continue
        commands.setdefault(command, []).append(item["id"])
    for command, ids in commands.items():
        if len(ids) > 1:
            warnings.append({"code": "duplicate_schedule", "message": command, "related_ids": ids})
    if any(row["status"] == "cleanup_pending" for row in restore_center.get("app_managed", [])):
        warnings.append({"code": "staging_cleanup_pending", "message": "Restore staging cleanup is pending"})
    return warnings


def latest_job_status(jobs: list[dict], operation_id: str) -> str:
    for job in jobs:
        if job.get("operation_id") == operation_id:
            return str(job.get("status", "unknown"))
    return "not_run"
```

Also extend `backup_manager/server.py` discovery assembly so inventory has real source data:

```python
if capabilities.get("systemd"):
    timers_output = read_remote(["systemctl", "list-timers", "--all", "--no-pager", "--no-legend"])
    payload["schedules"] = parse_systemd_timers(timers_output)
elif capabilities.get("cron"):
    cron_output = read_remote(["crontab", "-l"])
    payload["schedules"] = parse_crontab_lines(cron_output)
else:
    payload["schedules"] = []

if capabilities.get("restic") and config.restic.repository and config.restic.password_file:
    restic_result = command_executor.run_argv(
        ["env", f"RESTIC_REPOSITORY={config.restic.repository}", f"RESTIC_PASSWORD_FILE={config.restic.password_file}", "restic", "snapshots", "--json"]
    )
    payload["restic_snapshots"] = json.loads(restic_result.stdout) if restic_result.returncode == 0 else []
else:
    payload["restic_snapshots"] = []
```

- [ ] **Step 5: Manually run the tests and commit**

```powershell
py -m unittest tests.test_inventory tests.test_http_api tests.test_discovery -v
git add backup_manager/inventory.py backup_manager/discovery.py backup_manager/server.py tests/test_inventory.py tests/test_http_api.py tests/test_discovery.py
git commit -m "feat: surface backup tasks artifacts and warnings"
```

Expected: inventory now reports backup task rows, artifact placeholders, and duplicate-schedule warnings for the UI.

### Task 6: Render The Host-Aware UI And Document Manual Verification

**Files:**
- Modify: `static/app.js`
- Modify: `static/workflow.js`
- Modify: `static/styles.css`
- Modify: `README.md`

- [ ] **Step 1: Add UI smoke checks for the new script structure**

Add a manual verification section to the plan workspace by checking syntax only:

```powershell
node --check static/workflow.js
node --check static/app.js
```

Expected: both files parse before and after edits.

- [ ] **Step 2: Extend the frontend state and overview rendering**

Modify the top of `static/app.js`:

```javascript
const state = {
  config: null,
  discovery: null,
  jobs: [],
  workflow: null,
  profile: null,
  capabilities: null,
  inventory: null,
  sshPassword: "",
  connectionResult: null,
};
```

In `init()`:

```javascript
state.profile = payload.profile;
state.capabilities = payload.capabilities;
state.inventory = payload.inventory;
```

Update `renderOverview()` to show platform and capability badges:

```javascript
const profile = state.profile || { label: "Unknown Host", kind: "unknown" };
const capabilityBadges = Object.entries(state.capabilities || {})
  .filter(([, enabled]) => enabled)
  .map(([name]) => `<span class="capability-badge">${escapeHtml(name)}</span>`)
  .join("");
```

- [ ] **Step 3: Add a dedicated restore-center page section**

Add to `static/app.js`:

```javascript
function renderRestoreCenter() {
  const restoreCenter = state.inventory?.restore_center || { app_managed: [], external: [] };
  $("#restoreCenter").innerHTML = `
    ${BackupWorkflow.renderStepHeader("restore_center", state.workflow, "先恢复到暂存区，再核对，再复制或覆盖正式目录。", ["不要使用 /tmp", "优先使用独立恢复 dataset", "覆盖原位置前先核对暂存内容"])}
    <section class="band">
      <h3>本应用创建的暂存目录</h3>
      ${renderStagingTable(restoreCenter.app_managed, true)}
    </section>
    <section class="band">
      <h3>外部目录</h3>
      ${renderStagingTable(restoreCenter.external, false)}
    </section>
    ${BackupWorkflow.renderStepFooter("restore_center", state.workflow)}
  `;
}

function renderStagingTable(rows, appManaged) {
  if (!rows.length) {
    return `<p class="muted">未发现目录。</p>`;
  }
  return `
    <table class="inventory-table">
      <thead><tr><th>存在文件</th><th>名称</th><th>路径</th><th>来源快照</th><th>状态</th><th>操作</th></tr></thead>
      <tbody>
        ${rows.map((row) => `
          <tr>
            <td>${row.has_files ? "是" : "否"}</td>
            <td>${escapeHtml(row.name)}</td>
            <td>${escapeHtml(row.path)}</td>
            <td>${escapeHtml(row.snapshot_id || "未关联")}</td>
            <td><span class="status-chip">${escapeHtml(row.status)}</span></td>
            <td><button class="danger" onclick="promptDeleteStaging('${escapeAttr(row.path)}', ${appManaged})">删除</button></td>
          </tr>
        `).join("")}
      </tbody>
    </table>
  `;
}
```

- [ ] **Step 4: Render backup-task warnings and notification fields**

Add to `static/app.js`:

```javascript
function renderTaskSummary() {
  const tasks = state.inventory?.backup_tasks || [];
  const warnings = state.inventory?.warnings || [];
  $("#taskSummary").innerHTML = `
    <section class="band">
      <h3>已发现的备份任务</h3>
      ${tasks.length ? `
        <table class="inventory-table">
          <thead><tr><th>名称</th><th>类型</th><th>目标</th><th>最近结果</th></tr></thead>
          <tbody>
            ${tasks.map((task) => `
              <tr>
                <td>${escapeHtml(task.name)}</td>
                <td>${escapeHtml(task.type)}</td>
                <td>${escapeHtml(task.destination)}</td>
                <td>${escapeHtml(task.latest_result)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      ` : `<p class="muted">未发现任务。</p>`}
    </section>
    <section class="band">
      <h3>计划与告警</h3>
      ${warnings.length ? warnings.map((item) => `<p class="warning-line">${escapeHtml(item.code)}: ${escapeHtml(item.message)}</p>`).join("") : `<p class="muted">暂无告警。</p>`}
      <div class="grid">
        <div>
          <label>通知邮箱</label>
          <textarea id="notificationEmails">${escapeHtml((state.config.notification_emails || []).join("\n"))}</textarea>
        </div>
        <div>
          <label>发送人标识</label>
          <input id="notificationSender" value="${escapeAttr(state.config.notification_sender || "")}" placeholder="backup-manager@example.local">
        </div>
      </div>
    </section>
  `;
}
```

- [ ] **Step 5: Add delete-confirmation UX and documentation**

Add to `static/workflow.js`:

```javascript
const STEP_HELP = {
  restore_center: "恢复中心会先落到暂存目录，默认不自动删除。只有核对通过后，才建议继续复制、覆盖或清理。",
};
```

Add to `static/styles.css`:

```css
.capability-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.25rem 0.6rem;
  border-radius: 999px;
  background: #edf6f3;
  color: #245848;
  font-size: 0.82rem;
  margin-right: 0.35rem;
}

.inventory-table {
  width: 100%;
  border-collapse: collapse;
}

.inventory-table th,
.inventory-table td {
  padding: 0.8rem;
  border-bottom: 1px solid #d7ddd8;
  text-align: left;
  vertical-align: top;
}
```

Update `README.md` with:

```markdown
## Supported Targets

- OMV over SSH
- PVE over SSH
- Generic Linux over SSH
- The current local Windows machine

## Restore Staging Safety

- Never restore to `/tmp`
- Prefer a dedicated ZFS restore dataset when ZFS is available
- The restore center keeps app-managed and external staging directories separate
- Staging directories are not auto-deleted after restore

## Notification Settings

- Notification recipient input uses one email per line
- The first core release stores notification settings and warning state
- Actual outbound mail transport remains a follow-up integration after the host-aware core lands
```

- [ ] **Step 6: Manually check frontend syntax, inspect the diff, and commit**

```powershell
node --check static/workflow.js
node --check static/app.js
git add static/app.js static/workflow.js static/styles.css README.md
git commit -m "feat: render host-aware control center ui"
```

Expected: JavaScript parses, the README documents the new model, and the UI now exposes host profile, backup tasks, restore-center lists, notification fields, and safe cleanup controls.

## Self-Review Checklist

- Spec coverage: this plan covers platform detection, capability detection, restore-root management, restore-center task state, staging-directory visibility, task and artifact inventory, duplicate-schedule warnings, delete confirmation, workflow updates, state APIs, and host-aware UI. Remaining depth work such as PBS restore-drill evidence import and cloud-provider-specific onboarding can remain follow-up work only after this core lands.
- Placeholder scan: search this plan for `TODO`, `TBD`, `implement later`, `appropriate error handling`, or `similar to`. Remove any found before implementation.
- Type consistency: keep `restore_root`, `restore_center`, `profile`, `capabilities`, and `inventory` naming identical across config, API, workflow, and frontend.

## Manual Verification Sequence

After implementation, the operator should run these checks manually in order:

1. `py -m unittest tests.test_restore_center tests.test_profile tests.test_inventory tests.test_workflow tests.test_http_api tests.test_discovery -v`
2. `node --check static/workflow.js`
3. `node --check static/app.js`
4. Start the app in mock mode and confirm the overview shows platform, capabilities, and the restore-center step.
5. Confirm the overview or task summary area shows discovered backup tasks, warnings, and notification fields.
6. Switch to SSH mode against an OMV or Linux fixture host and confirm storage candidates plus restore-root candidates appear.
7. Confirm the restore-center page separates app-managed and external directories.
8. Confirm the delete dialog for external directories requires stronger confirmation text.
