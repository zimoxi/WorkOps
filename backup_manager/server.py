from __future__ import annotations

from dataclasses import asdict
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path, PurePosixPath
import platform
import shutil
import threading
import time
from typing import Any
from urllib.parse import parse_qs, urlparse

from .commands import CommandCatalog, OperationError
from .config import AppConfig, ConfigStore
from .discovery import (
    list_first_level_folders,
    local_windows_drives,
    mock_storage,
    parse_crontab_lines,
    parse_df,
    parse_remote_folders,
    parse_systemd_timers,
    parse_zfs_list,
    parse_zpool_list,
    suggest_restore_root_candidates,
    suggest_storage_targets,
)
from .executor import LocalExecutor, MockExecutor, SshConnection, SshExecutor
from .inventory import build_inventory
from .jobs import JobRecord, JobStore, now_iso
from .profile import (
    detect_local_platform,
    detect_remote_capabilities,
    detect_remote_platform,
)
from .restore_center import RestoreStore, summarize_staging_entries
from .workflow import derive_workflow
from .device_repository import DeviceRepository
from .device_service import DeviceService
from .auth_service import validate_user, create_session, get_session, destroy_session, SESSION_COOKIE_NAME
from .api import handle_api_request, ApiError, error_response
from .repositories import MockDeviceRepository, MockResourceRepository, MockOperationRepository, MockTaskRepository
from .services import (
    DeviceService as ApiDeviceService,
    ResourceService,
    OperationService,
    TaskService,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent
OPTIONAL_WORKFLOW_STEPS = {"dataset", "windows", "cloud", "pve_pbs"}
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
CONNECTION_ERROR_CODES = {
    "authentication_failed",
    "host_key_failed",
    "host_key_unknown",
    "connection_timeout",
    "connection_refused",
    "host_unreachable",
    "client_missing",
    "invalid_connection",
}
NON_PERSISTED_CONFIG_KEYS = {
    "ssh_password",
    "password",
    "pass",
    "secret",
    "secret_access_key",
    "access_key_id",
    "bearer_token",
    "session_token",
    "api_key",
    "api_secret",
    "token",
    "refresh_token",
    "client_secret",
    "client_id",
}
OPERATION_STEP_MAP = {
    "restic-backup": "first_backup",
    "restic-restore": "restore_center",
    "restic-snapshots": "restic",
    "restic-check": "schedule",
    "restic-prune": "schedule",
    "restore-staging-delete": "restore_center",
    "migration-create-temp": "dataset",
    "migration-rsync": "dataset",
    "cloud-rclone-check": "cloud",
    "cloud-rclone-list": "cloud",
    "cloud-rclone-pull": "cloud",
    "cloud-rclone-sync": "cloud",
    "pve-list-guests": "pve_pbs",
    "pve-vzdump": "pve_pbs",
    "windows-robocopy-preview": "windows",
}


class AppContext:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.config_store = ConfigStore(data_dir / "config.json")
        self.job_store = JobStore(data_dir / "jobs.jsonl")
        self.restore_store = RestoreStore(data_dir / "restore_tasks.json")
        self.catalog = CommandCatalog()
        self.job_lock = threading.Lock()
        self.running_jobs: dict[str, dict[str, Any]] = {}
        self.job_payloads: dict[str, dict[str, Any]] = {}
        # Device domain (Sprint002)
        self._sqlite_device_repo = DeviceRepository(data_dir / "workops.db")
        self.device_service = DeviceService(self._sqlite_device_repo)
        self.device_service.ensure_mock_data()
        
        # Mock data for API Layer (Sprint014)
        self.resources = [
            {"id": "r-001", "device_id": "dev-001", "name": "Disk C", "type": "disk", "path": "C:\\", "mount_point": "C:\\", "size_total": "512GB", "size_used": "320GB", "status": "online"},
            {"id": "r-002", "device_id": "dev-001", "name": "Disk D", "type": "disk", "path": "D:\\", "mount_point": "D:\\", "size_total": "2TB", "size_used": "1.2TB", "status": "online"},
            {"id": "r-003", "device_id": "dev-002", "name": "Pool tank", "type": "dataset", "path": "tank", "mount_point": "/mnt/tank", "size_total": "16TB", "size_used": "8.5TB", "status": "online"},
        ]
        self.operations = [
            {"id": "op-001", "name": "Daily Backup", "type": "backup", "device_id": "dev-001", "resource_id": "r-001", "schedule": "daily", "last_run": "2026-07-04 02:00", "status": "success"},
            {"id": "op-002", "name": "NAS Photos Backup", "type": "backup", "device_id": "dev-002", "resource_id": "r-003", "schedule": "weekly", "last_run": "2026-07-01 03:00", "status": "success"},
        ]
        self.tasks = [
            {"id": "task-001", "operation_id": "op-001", "operation_name": "Daily Backup", "device_id": "dev-001", "status": "success", "start_time": "2026-07-04 02:00", "end_time": "2026-07-04 02:05:30", "duration": "5m30s"},
            {"id": "task-002", "operation_id": "op-002", "operation_name": "NAS Photos Backup", "device_id": "dev-002", "status": "success", "start_time": "2026-07-01 03:00", "end_time": "2026-07-01 03:15:00", "duration": "15m00s"},
        ]
        
        # Repository Layer (Sprint016)
        # 包装现有 Mock 数据，不复制新数据
        self._device_repo = MockDeviceRepository(self)
        self._resource_repo = MockResourceRepository(self)
        self._operation_repo = MockOperationRepository(self)
        self._task_repo = MockTaskRepository(self)
        
        # Service Layer (Sprint016)
        # 调用 Repository
        self.api_device_service = ApiDeviceService(self._device_repo)
        self.api_resource_service = ResourceService(self._resource_repo)
        self.api_operation_service = OperationService(self._operation_repo)
        self.api_task_service = TaskService(self._task_repo)

    def close(self) -> None:
        """Close database connections. Idempotent."""
        if hasattr(self, '_sqlite_device_repo'):
            self._sqlite_device_repo.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def runtime_flags_from_profile(profile_payload: dict[str, object]) -> dict[str, object]:
    kind = str(profile_payload.get("kind", "linux"))
    return {
        "local_platform": "windows" if kind == "windows-local" else "linux",
        "host_platform": kind,
    }


def build_summary(config: AppConfig) -> dict[str, Any]:
    storage = config.active_storage()
    restore_root = config.active_restore_root()
    return {
        "executor_mode": config.executor_mode,
        "active_storage": storage.name if storage else "",
        "mountpoint": storage.mountpoint if storage else "",
        "restic_repository": config.restic.repository,
        "restore_root": restore_root.path if restore_root else "",
        "backup_sets": len(config.backup_sets),
        "pve_enabled": config.pve_pbs.enabled,
        "cloud_enabled": config.cloud_remote.enabled,
    }


def probe_local_command_presence() -> dict[str, bool]:
    return {name: shutil.which(name) is not None for name in PROFILE_PROBE_COMMANDS}


def probe_command_presence(command_executor) -> dict[str, bool]:
    result: dict[str, bool] = {}
    for name in PROFILE_PROBE_COMMANDS:
        probe = command_executor.run_argv(
            ["sh", "-lc", f"command -v {name} >/dev/null 2>&1"]
        )
        result[name] = probe.returncode == 0
    return result


def discover_profile(
    config: AppConfig, executor=None
) -> tuple[dict[str, object], dict[str, bool]]:
    if config.platform_override:
        presence = (
            probe_local_command_presence()
            if config.executor_mode == "local"
            else probe_command_presence(executor or create_executor(config))
        )
        return (
            {
                "kind": config.platform_override,
                "label": config.platform_override,
                "source": "override",
            },
            detect_remote_capabilities(presence),
        )

    if config.executor_mode == "mock":
        return (
            {"kind": "omv", "label": "Mock OMV Host", "source": "mock"},
            {
                "zfs": True,
                "restic": True,
                "rclone": True,
                "systemd": True,
                "cron": False,
                "pbs": False,
                "smb": True,
            },
        )

    if config.executor_mode == "local":
        profile_payload = detect_local_platform(platform.system())
        return profile_payload, detect_remote_capabilities(probe_local_command_presence())

    command_executor = executor or create_executor(config)
    presence = probe_command_presence(command_executor)
    return detect_remote_platform(presence), detect_remote_capabilities(presence)


def discover_storage(
    config: AppConfig,
    executor=None,
    profile_payload: dict[str, object] | None = None,
    capabilities: dict[str, bool] | None = None,
) -> dict[str, Any]:
    if config.executor_mode == "mock":
        result = mock_storage()
        result["errors"] = []
        return result

    command_executor = executor or create_executor(config)
    if profile_payload is None or capabilities is None:
        detected_profile, detected_capabilities = discover_profile(
            config, command_executor
        )
        if profile_payload is None:
            profile_payload = detected_profile
        if capabilities is None:
            capabilities = detected_capabilities
    errors: list[dict[str, str]] = []

    def read_remote(argv: list[str]) -> str:
        result = command_executor.run_argv(argv)
        if result.returncode:
            error = result.error or {
                "code": "command_failed",
                "message": f"Command failed: {argv[0]}",
                "recovery": result.stderr.strip()
                or "Check the remote environment and account permissions.",
            }
            errors.append(error)
            return ""
        return result.stdout

    if profile_payload.get("kind") == "windows-local":
        active = config.active_storage()
        folders = list_first_level_folders(active.mountpoint) if active else []
        restore_root = config.active_restore_root()
        restore_stage_entries = (
            summarize_staging_entries(
                restore_root.path, list_first_level_folders(restore_root.path)
            )
            if restore_root
            else []
        )
        return {
            "pools": [],
            "datasets": [],
            "mounts": [],
            "folders": folders,
            "storage_candidates": [],
            "restore_root_candidates": [],
            "restore_stage_entries": restore_stage_entries,
            "windows_drives": local_windows_drives(),
            "schedules": [],
            "restic_snapshots": [],
            "pbs_backups": [],
            "errors": errors,
        }

    pools_output = ""
    datasets_output = ""
    if capabilities.get("zfs"):
        pools_output = read_remote(
            ["zpool", "list", "-H", "-o", "name,size,allocated,free,health"]
        )
        datasets_output = read_remote(
            ["zfs", "list", "-H", "-o", "name,mountpoint,used,avail"]
        )
    mounts_output = read_remote(["df", "-h"])
    parsed_datasets = parse_zfs_list(datasets_output)
    active = config.active_storage()
    folders: list[dict[str, str]] = []
    if active:
        folders_output = read_remote(
            [
                "find",
                active.mountpoint,
                "-mindepth",
                "1",
                "-maxdepth",
                "1",
                "-type",
                "d",
                "-printf",
                "%f\t%p\n",
            ]
        )
        folders = parse_remote_folders(folders_output)

    restore_root = config.active_restore_root()
    restore_stage_entries: list[dict[str, object]] = []
    if restore_root:
        stage_output = read_remote(
            [
                "find",
                restore_root.path,
                "-mindepth",
                "1",
                "-maxdepth",
                "1",
                "-type",
                "d",
                "-printf",
                "%f\t%p\n",
            ]
        )
        restore_stage_entries = summarize_staging_entries(
            restore_root.path,
            [
                {"name": item["name"], "path": item["path"], "has_files": True}
                for item in parse_remote_folders(stage_output)
            ],
        )

    schedules: list[dict[str, str]] = []
    if capabilities.get("systemd"):
        schedules = parse_systemd_timers(
            read_remote(["systemctl", "list-timers", "--all", "--no-pager", "--no-legend"])
        )
    elif capabilities.get("cron"):
        schedules = parse_crontab_lines(read_remote(["crontab", "-l"]))

    restic_snapshots: list[dict[str, object]] = []
    if (
        capabilities.get("restic")
        and config.restic.repository
        and config.restic.password_file
    ):
        restic_result = command_executor.run_argv(
            [
                "env",
                f"RESTIC_REPOSITORY={config.restic.repository}",
                f"RESTIC_PASSWORD_FILE={config.restic.password_file}",
                "restic",
                "snapshots",
                "--json",
            ]
        )
        if restic_result.returncode == 0:
            try:
                restic_snapshots = json.loads(restic_result.stdout)
            except json.JSONDecodeError:
                restic_snapshots = []

    return {
        "pools": parse_zpool_list(pools_output),
        "datasets": parsed_datasets,
        "mounts": parse_df(mounts_output),
        "folders": folders,
        "storage_candidates": suggest_storage_targets(parsed_datasets),
        "restore_root_candidates": suggest_restore_root_candidates(parsed_datasets),
        "restore_stage_entries": restore_stage_entries,
        "windows_drives": local_windows_drives(),
        "schedules": schedules,
        "restic_snapshots": restic_snapshots,
        "pbs_backups": [],
        "errors": errors,
    }


def build_state_inventory(
    context: AppContext,
    config: AppConfig,
    discovery: dict[str, object],
    profile_payload: dict[str, object],
    capabilities: dict[str, bool],
) -> dict[str, object]:
    return build_inventory(
        config=config.to_dict(),
        profile=profile_payload,
        capabilities=capabilities,
        discovery=discovery,
        restore_tasks=context.restore_store.list_tasks(),
        staging_entries=discovery.get("restore_stage_entries", []),
        jobs=context.job_store.latest(),
    )


def lightweight_profile_and_capabilities(
    config: AppConfig,
) -> tuple[dict[str, object], dict[str, bool], dict[str, object]]:
    if config.executor_mode == "mock":
        profile_payload, capabilities = discover_profile(config)
        return profile_payload, capabilities, mock_storage()
    if config.executor_mode == "local":
        profile_payload = detect_local_platform(platform.system())
        capabilities = detect_remote_capabilities(probe_local_command_presence())
        discovery: dict[str, object] = {
            "pools": [],
            "datasets": [],
            "mounts": [],
            "folders": [],
            "storage_candidates": [],
            "restore_root_candidates": [],
            "restore_stage_entries": [],
            "windows_drives": local_windows_drives(),
            "schedules": [],
            "restic_snapshots": [],
            "pbs_backups": [],
            "errors": [],
        }
        return profile_payload, capabilities, discovery
    profile_payload = {
        "kind": config.platform_override or "linux",
        "label": config.platform_override or "Remote Host",
        "source": "config",
    }
    capabilities = {
        "zfs": False,
        "restic": False,
        "rclone": False,
        "systemd": False,
        "cron": False,
        "pbs": False,
        "smb": False,
    }
    discovery = {
        "pools": [],
        "datasets": [],
        "mounts": [],
        "folders": [],
        "storage_candidates": [],
        "restore_root_candidates": [],
        "restore_stage_entries": [],
        "windows_drives": [],
        "schedules": [],
        "restic_snapshots": [],
        "pbs_backups": [],
        "errors": [],
    }
    return profile_payload, capabilities, discovery


def json_response_payload(context: AppContext) -> dict[str, Any]:
    config = context.config_store.load()
    jobs = context.job_store.latest()
    profile_payload, capabilities, discovery = lightweight_profile_and_capabilities(
        config
    )
    inventory = build_state_inventory(
        context, config, discovery, profile_payload, capabilities
    )
    return {
        "config": config.to_dict(),
        "operations": context.catalog.operations(),
        "jobs": jobs,
        "summary": build_summary(config),
        "profile": profile_payload,
        "capabilities": capabilities,
        "inventory": inventory,
        "workflow": derive_workflow(
            config, jobs, runtime_flags_from_profile(profile_payload)
        ),
    }


def config_response_payload(context: AppContext, config: AppConfig) -> dict[str, Any]:
    jobs = context.job_store.latest()
    profile_payload, capabilities, discovery = lightweight_profile_and_capabilities(
        config
    )
    inventory = build_state_inventory(
        context, config, discovery, profile_payload, capabilities
    )
    return {
        "config": config.to_dict(),
        "summary": build_summary(config),
        "profile": profile_payload,
        "capabilities": capabilities,
        "inventory": inventory,
        "workflow": derive_workflow(
            config, jobs, runtime_flags_from_profile(profile_payload)
        ),
    }


def mark_workflow_evidence(
    context: AppContext, key: str, config: AppConfig | None = None
) -> AppConfig:
    current = config or context.config_store.load()
    current.workflow.completed_at[key] = now_iso()
    context.config_store.save(current)
    return current


def discovery_has_connection_success(payload: dict[str, Any]) -> bool:
    if not payload.get("pools") and not payload.get("datasets"):
        if not payload.get("windows_drives"):
            return False
    return not any(
        error.get("code") in CONNECTION_ERROR_CODES
        for error in payload.get("errors", [])
    )


def sanitize_config_patch(payload: dict[str, Any]) -> dict[str, Any]:
    def clean_mapping(mapping: dict[str, Any]) -> dict[str, Any]:
        cleaned: dict[str, Any] = {}
        for key, value in mapping.items():
            if key in NON_PERSISTED_CONFIG_KEYS:
                continue
            if isinstance(value, dict):
                cleaned[key] = clean_mapping(value)
            elif isinstance(value, list):
                cleaned[key] = [
                    clean_mapping(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                cleaned[key] = value
        return cleaned

    return clean_mapping(payload)


def is_restore_path_inside_root(root_path: str, candidate_path: str) -> bool:
    root = str(PurePosixPath(root_path or ""))
    candidate = str(PurePosixPath(candidate_path or ""))
    if not root or not candidate or candidate == root:
        return False
    return candidate.startswith(root.rstrip("/") + "/")


def restore_task_id_for_path(path: str) -> str:
    name = PurePosixPath(path).name.strip() or f"restore-{int(time.time())}"
    return f"restore-{name}"


def update_restore_store_after_job(
    context: AppContext,
    config: AppConfig,
    operation_id: str,
    payload: dict[str, Any],
    succeeded: bool,
    finished_at: str,
) -> None:
    if not succeeded:
        return

    restore_root = config.active_restore_root()
    if operation_id == "restic-restore":
        target = str(PurePosixPath(str(payload.get("target", "")).strip()))
        if not restore_root or not is_restore_path_inside_root(restore_root.path, target):
            return
        existing = context.restore_store.find_task_by_staging_path(target) or {}
        context.restore_store.save_task(
            {
                "id": existing.get("id") or restore_task_id_for_path(target),
                "snapshot_id": str(payload.get("snapshot", "latest")).strip() or "latest",
                "selected_paths": [
                    str(item).strip()
                    for item in payload.get("paths", [])
                    if str(item).strip()
                ],
                "staging_name": PurePosixPath(target).name or target,
                "staging_path": target,
                "status": "restored_pending_review",
                "origin": "app_managed",
                "created_at": existing.get("created_at") or finished_at,
                "target_path": target,
            }
        )
        return

    if operation_id == "restore-staging-delete":
        target = str(PurePosixPath(str(payload.get("target", "")).strip()))
        existing = context.restore_store.find_task_by_staging_path(target)
        if not existing:
            return
        updated = dict(existing)
        updated["status"] = "cleanup_complete"
        updated["target_path"] = target
        context.restore_store.save_task(updated)


def update_cloud_remote_after_job(
    context: AppContext,
    config: AppConfig,
    operation_id: str,
    succeeded: bool,
    finished_at: str,
) -> AppConfig:
    if not succeeded:
        return config
    if operation_id not in {"cloud-rclone-check", "cloud-rclone-sync"}:
        return config

    config.cloud_remote.verified_at = finished_at
    config.workflow.completed_at["cloud"] = finished_at
    context.config_store.save(config)
    return config


def update_workflow_step(
    context: AppContext, body: dict[str, Any]
) -> tuple[dict[str, Any], HTTPStatus]:
    step_id = str(body.get("step_id", "")).strip()
    action = str(body.get("action", "")).strip()
    if step_id not in OPTIONAL_WORKFLOW_STEPS:
        return {"error": "This step cannot be skipped."}, HTTPStatus.BAD_REQUEST
    if action not in {"skip", "reopen"}:
        return {"error": "Unsupported workflow action."}, HTTPStatus.BAD_REQUEST

    config = context.config_store.load()
    if action == "skip":
        reason = str(body.get("reason", "")).strip()
        if not reason:
            return {"error": "Skip reason is required."}, HTTPStatus.BAD_REQUEST
        if len(reason) > 200:
            return {"error": "Skip reason must be 200 characters or fewer."}, HTTPStatus.BAD_REQUEST
        config.workflow.skipped_steps[step_id] = reason
    else:
        config.workflow.skipped_steps.pop(step_id, None)

    context.config_store.save(config)
    response = config_response_payload(context, config)
    step = next(item for item in response["workflow"]["steps"] if item["id"] == step_id)
    response["step"] = step
    return response, HTTPStatus.OK


def probe_ssh_connection(executor) -> dict[str, Any]:
    result = executor.run_argv(["printf", "backup-manager-ok"])
    ok = result.returncode == 0 and result.stdout.strip() == "backup-manager-ok"
    if ok:
        return {"ok": True, "message": "SSH connection succeeded.", "error": None}
    error = result.error or {
        "code": "unexpected_response",
        "message": "SSH returned an unexpected result.",
        "recovery": "Check the remote shell configuration and account permissions.",
    }
    return {
        "ok": False,
        "message": error["message"],
        "error": error,
        "stderr": result.stderr.strip(),
    }


def create_executor(config: AppConfig, password: str = ""):
    if config.executor_mode == "local":
        return LocalExecutor()
    if config.executor_mode == "ssh":
        return SshExecutor(
            SshConnection(
                host=config.ssh_host,
                user=config.ssh_user,
                port=config.ssh_port,
                auth_mode=config.ssh_auth_mode,
                key_path=config.ssh_key_path,
                password=password,
            )
        )
    return MockExecutor()


def new_job_id() -> str:
    return f"job-{time.time_ns()}"


def running_job_payload(job_id: str, command: Any, started: str) -> dict[str, Any]:
    return {
        "id": job_id,
        "operation_id": command.id,
        "title": command.title,
        "started_at": started,
        "finished_at": "",
        "status": "running",
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "command": command.argv,
        "step_id": OPERATION_STEP_MAP.get(command.id, "connect"),
        "metadata": {
            "progress": {
                "percent": None,
                "detail": "Command is running. Waiting for output.",
            }
        },
    }


def failed_job_payload(
    job_id: str, command: Any, started: str, message: str
) -> dict[str, Any]:
    finished = now_iso()
    record = JobRecord(
        id=job_id,
        operation_id=command.id,
        title=command.title,
        started_at=started,
        finished_at=finished,
        status="failed",
        returncode=1,
        stdout="",
        stderr=message,
        command=command.argv,
        step_id=OPERATION_STEP_MAP.get(command.id, "connect"),
        metadata={"progress": {"percent": None, "detail": "Failed before output."}},
    )
    return {"job": record.to_dict(), "error": message}


def execute_command_payload(
    context: AppContext,
    command: Any,
    payload: dict[str, Any],
    ssh_password: str,
    job_id: str | None = None,
    started: str | None = None,
) -> dict[str, Any]:
    started = started or now_iso()
    result = create_executor(context.config_store.load(), ssh_password).run(command)
    finished = now_iso()
    record = JobRecord(
        id=job_id or new_job_id(),
        operation_id=command.id,
        title=command.title,
        started_at=started,
        finished_at=finished,
        status="success" if result.returncode == 0 else "failed",
        returncode=result.returncode,
        stdout=result.stdout,
        stderr=result.stderr,
        command=result.command,
        step_id=OPERATION_STEP_MAP.get(command.id, "connect"),
        metadata={
            "progress": {
                "percent": 100 if result.returncode == 0 else None,
                "detail": "Command finished.",
            }
        },
    )
    context.job_store.append(record)
    config = context.config_store.load()
    update_restore_store_after_job(
        context,
        config,
        command.id,
        payload,
        result.returncode == 0,
        finished,
    )
    config = update_cloud_remote_after_job(
        context,
        config,
        command.id,
        result.returncode == 0,
        finished,
    )
    profile_payload, capabilities = discover_profile(config)
    discovery = discover_storage(
        config,
        profile_payload=profile_payload,
        capabilities=capabilities,
    )
    inventory = build_state_inventory(
        context, config, discovery, profile_payload, capabilities
    )
    return {
        "result": result.to_dict(),
        "job": record.to_dict(),
        "config": config.to_dict(),
        "profile": profile_payload,
        "capabilities": capabilities,
        "inventory": inventory,
        "workflow": derive_workflow(
            config,
            context.job_store.latest(),
            runtime_flags_from_profile(profile_payload),
        ),
    }


def start_async_job(
    context: AppContext,
    command: Any,
    payload: dict[str, Any],
    ssh_password: str,
) -> dict[str, Any]:
    job_id = new_job_id()
    started = now_iso()
    job = running_job_payload(job_id, command, started)
    with context.job_lock:
        context.running_jobs[job_id] = job
        context.job_payloads[job_id] = {"job": job}

    def worker() -> None:
        try:
            final_payload = execute_command_payload(
                context, command, payload, ssh_password, job_id=job_id, started=started
            )
        except Exception as exc:  # pragma: no cover - defensive safety net
            final_payload = failed_job_payload(job_id, command, started, str(exc))
        with context.job_lock:
            context.running_jobs[job_id] = final_payload["job"]
            context.job_payloads[job_id] = final_payload

    threading.Thread(target=worker, daemon=True).start()
    return job


def make_handler(context: AppContext):
    class WorkOpsHandler(BaseHTTPRequestHandler):
        server_version = "WorkOps/1.0"

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.send_text(INDEX_HTML, "text/html; charset=utf-8")
                return
            if parsed.path == "/api/state":
                self.send_json(json_response_payload(context))
                return
            if parsed.path.startswith("/api/jobs/"):
                job_id = parsed.path.removeprefix("/api/jobs/")
                with context.job_lock:
                    payload = context.job_payloads.get(job_id)
                if payload:
                    self.send_json(payload)
                else:
                    self.send_json({"error": "job not found"}, HTTPStatus.NOT_FOUND)
                return
            if parsed.path == "/api/discover":
                config = context.config_store.load()
                profile_payload, capabilities = discover_profile(config)
                payload = discover_storage(
                    config,
                    profile_payload=profile_payload,
                    capabilities=capabilities,
                )
                if discovery_has_connection_success(payload):
                    mark_workflow_evidence(context, "storage_discovery", config)
                self.send_json(payload)
                return
            if parsed.path == "/api/restore-center":
                config = context.config_store.load()
                profile_payload, capabilities = discover_profile(config)
                discovery = discover_storage(
                    config,
                    profile_payload=profile_payload,
                    capabilities=capabilities,
                )
                inventory = build_state_inventory(
                    context, config, discovery, profile_payload, capabilities
                )
                self.send_json(inventory["restore_center"])
                return
            if parsed.path == "/api/folders":
                query = parse_qs(parsed.query)
                mountpoint = query.get("mountpoint", [""])[0]
                self.send_json({"folders": list_first_level_folders(mountpoint)})
                return
            if parsed.path.startswith("/static/"):
                self.serve_static(parsed.path.removeprefix("/static/"))
                return
            # Auth API (Sprint013)
            if parsed.path == "/api/auth/me":
                session_id = self.get_cookie(SESSION_COOKIE_NAME)
                session = get_session(session_id)
                if session:
                    self.send_json({"success": True, "data": {"user": {"id": session["user_id"], "username": session["username"], "role": session["role"], "enabled": True}}})
                else:
                    self.send_json({"success": False, "error": "Not authenticated"}, HTTPStatus.UNAUTHORIZED)
                return
            # API v1 (Sprint014)
            if parsed.path.startswith("/api/v1/"):
                try:
                    # 获取当前用户 (Sprint015)
                    session_id = self.get_cookie(SESSION_COOKIE_NAME)
                    session = get_session(session_id)
                    user = None
                    if session:
                        user = {
                            "id": session.get("user_id"),
                            "username": session.get("username"),
                            "role": session.get("role"),
                        }
                    
                    query_params = {k: v[0] for k, v in parse_qs(parsed.query).items()}
                    result = handle_api_request("GET", parsed.path, query_params, context, user)
                    self.send_json(result)
                except ApiError as e:
                    self.send_json(error_response(e.code, e.message), HTTPStatus(e.status_code))
                except Exception as e:
                    self.send_json(error_response("INTERNAL_ERROR", str(e)), HTTPStatus.INTERNAL_SERVER_ERROR)
                return
            # Device API (Sprint002)
            if parsed.path == "/api/devices":
                devices = context.device_service.list_devices()
                self.send_json({"devices": devices})
                return
            if parsed.path.startswith("/api/devices/"):
                device_id = parsed.path.removeprefix("/api/devices/")
                device = context.device_service.get_device(device_id)
                if device:
                    self.send_json({"device": device})
                else:
                    self.send_json({"error": "device not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:
            parsed = urlparse(self.path)
            try:
                body = self.read_json()
                # Auth API (Sprint013)
                if parsed.path == "/api/auth/login":
                    username = body.get("username", "")
                    password = body.get("password", "")
                    user = validate_user(username, password)
                    if user:
                        session_id = create_session(user)
                        self.send_response(HTTPStatus.OK)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Set-Cookie", f"{SESSION_COOKIE_NAME}={session_id}; Path=/; HttpOnly; SameSite=Lax")
                        self.end_headers()
                        self.wfile.write(json.dumps({"success": True, "data": {"user": user}}).encode())
                    else:
                        self.send_json({"success": False, "error": "Invalid username or password"}, HTTPStatus.UNAUTHORIZED)
                    return
                if parsed.path == "/api/auth/logout":
                    session_id = self.get_cookie(SESSION_COOKIE_NAME)
                    if session_id:
                        destroy_session(session_id)
                    self.send_response(HTTPStatus.OK)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Set-Cookie", f"{SESSION_COOKIE_NAME}=; Path=/; HttpOnly; Expires=Thu, 01 Jan 1970 00:00:00 GMT")
                    self.end_headers()
                    self.wfile.write(json.dumps({"success": True}).encode())
                    return
                if parsed.path == "/api/config":
                    config = context.config_store.update(sanitize_config_patch(body))
                    self.send_json(config_response_payload(context, config))
                    return
                if parsed.path == "/api/workflow/step":
                    payload, status = update_workflow_step(context, body)
                    self.send_json(payload, status)
                    return
                if parsed.path == "/api/test-ssh":
                    config = context.config_store.load()
                    if config.executor_mode != "ssh":
                        self.send_json(
                            {"error": "Switch executor mode to SSH first."},
                            HTTPStatus.BAD_REQUEST,
                        )
                        return
                    executor = create_executor(config, body.get("ssh_password", ""))
                    payload = probe_ssh_connection(executor)
                    if payload["ok"]:
                        config = mark_workflow_evidence(context, "ssh_test", config)
                        profile_payload, _ = discover_profile(config, executor)
                        payload["workflow"] = derive_workflow(
                            config,
                            context.job_store.latest(),
                            runtime_flags_from_profile(profile_payload),
                        )
                    self.send_json(
                        payload,
                        HTTPStatus.OK if payload["ok"] else HTTPStatus.BAD_GATEWAY,
                    )
                    return
                if parsed.path == "/api/discover":
                    config = context.config_store.load()
                    executor = create_executor(config, body.get("ssh_password", ""))
                    profile_payload, capabilities = discover_profile(config, executor)
                    payload = discover_storage(
                        config,
                        executor=executor,
                        profile_payload=profile_payload,
                        capabilities=capabilities,
                    )
                    if discovery_has_connection_success(payload):
                        config = mark_workflow_evidence(
                            context, "storage_discovery", config
                        )
                        payload["workflow"] = derive_workflow(
                            config,
                            context.job_store.latest(),
                            runtime_flags_from_profile(profile_payload),
                        )
                    payload["profile"] = profile_payload
                    payload["capabilities"] = capabilities
                    payload["inventory"] = build_state_inventory(
                        context, config, payload, profile_payload, capabilities
                    )
                    self.send_json(payload)
                    return
                if parsed.path == "/api/prepare":
                    command = context.catalog.build(
                        body.get("operation_id", ""), body.get("payload", {})
                    )
                    self.send_json({"command": asdict(command)})
                    return
                if parsed.path == "/api/run":
                    operation_id = body.get("operation_id", "")
                    payload = body.get("payload", {})
                    command = context.catalog.build(operation_id, payload)
                    if command.confirm_text and body.get("confirmation") != command.confirm_text:
                        self.send_json(
                            {
                                "error": "confirmation_required",
                                "command": asdict(command),
                                "required": command.confirm_text,
                            },
                            HTTPStatus.CONFLICT,
                        )
                        return
                    if body.get("async"):
                        job = start_async_job(
                            context,
                            command,
                            payload,
                            body.get("ssh_password", ""),
                        )
                        self.send_json({"job": job, "async": True}, HTTPStatus.ACCEPTED)
                        return
                    self.send_json(
                        execute_command_payload(
                            context,
                            command,
                            payload,
                            body.get("ssh_password", ""),
                        )
                    )
                    return
                # Device API - Create (Sprint002)
                if parsed.path == "/api/devices":
                    try:
                        device = context.device_service.create_device(body)
                        self.send_json({"device": device}, HTTPStatus.CREATED)
                    except ValueError as exc:
                        self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_error(HTTPStatus.NOT_FOUND)
            except OperationError as exc:
                self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self.send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_PUT(self) -> None:
            parsed = urlparse(self.path)
            try:
                body = self.read_json()
                # Device API - Update (Sprint002)
                if parsed.path.startswith("/api/devices/"):
                    device_id = parsed.path.removeprefix("/api/devices/")
                    try:
                        device = context.device_service.update_device(device_id, body)
                        if device:
                            self.send_json({"device": device})
                        else:
                            self.send_json({"error": "device not found"}, HTTPStatus.NOT_FOUND)
                    except ValueError as exc:
                        self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)
                    return
                self.send_error(HTTPStatus.NOT_FOUND)
            except json.JSONDecodeError:
                self.send_json({"error": "invalid json"}, HTTPStatus.BAD_REQUEST)

        def do_DELETE(self) -> None:
            parsed = urlparse(self.path)
            # Device API - Delete (Sprint002)
            if parsed.path.startswith("/api/devices/"):
                device_id = parsed.path.removeprefix("/api/devices/")
                if context.device_service.delete_device(device_id):
                    self.send_json({"ok": True})
                else:
                    self.send_json({"error": "device not found"}, HTTPStatus.NOT_FOUND)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def get_cookie(self, name: str) -> str:
            """从 Cookie 中获取指定名称的值"""
            cookie_header = self.headers.get("Cookie", "")
            if not cookie_header:
                return ""
            for part in cookie_header.split(";"):
                part = part.strip()
                if part.startswith(name + "="):
                    return part[len(name) + 1:]
            return ""

        def read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("content-length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length else "{}"
            return json.loads(raw or "{}")

        def send_json(
            self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK
        ) -> None:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def send_text(self, text: str, content_type: str) -> None:
            data = text.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def serve_static(self, relative: str) -> None:
            path = (PROJECT_ROOT / "static" / relative).resolve()
            static_root = (PROJECT_ROOT / "static").resolve()
            if not str(path).startswith(str(static_root)) or not path.exists():
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            content_type = (
                mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            )
            data = path.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return WorkOpsHandler


def run_server(
    host: str = "127.0.0.1", port: int = 8099, data_dir: Path | None = None
) -> None:
    data_path = data_dir or Path(
        os.environ.get("WORKOPS_DATA", os.environ.get("BACKUP_MANAGER_DATA", PROJECT_ROOT / "data"))
    )
    context = AppContext(data_path)
    server = ThreadingHTTPServer((host, port), make_handler(context))
    print(f"WorkOps listening on http://{host}:{port}")
    server.serve_forever()


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WorkOps</title>
  <link rel="stylesheet" href="/static/styles.css">
  <link rel="stylesheet" href="/static/components/styles.css">
</head>
<body>
  <button id="menuToggle" class="menu-toggle" onclick="toggleMenu()">☰</button>
  <div id="menuOverlay" class="menu-overlay" onclick="toggleMenu()"></div>
  <aside class="side" id="sidebar">
    <header class="app-header">
      <div class="brand">WorkOps</div>
      <div class="header-right">
        <span class="header-icon" data-i18n="header.search" title="搜索">🔍</span>
        <span class="header-icon" data-i18n="header.notify" title="通知">🔔</span>
      </div>
    </header>
    <div id="langSwitcher" class="lang-switcher-container"></div>
    <div id="userBadge" class="user-badge-container"></div>
    <button data-page="workspace" class="nav active" data-i18n="nav.workspace">工作台</button>
    <button data-page="overview" class="nav" data-i18n="nav.overview">总览</button>
    <button data-page="devices" class="nav" data-i18n="nav.devices">设备</button>
    <button data-page="resources" class="nav" data-i18n="nav.resources">资源</button>
    <button data-page="operations" class="nav" data-i18n="nav.operations">操作</button>
    <button data-page="tasks" class="nav" data-i18n="nav.tasks">任务</button>
    <button data-page="monitoring" class="nav" data-i18n="nav.monitoring">监控</button>
    <button data-page="scheduler" class="nav" data-i18n="nav.scheduler">调度</button>
    <button data-page="history" class="nav" data-i18n="nav.history">历史</button>
    <button data-page="storage" class="nav" data-i18n="nav.storage">连接与存储</button>
    <button data-page="restore" class="nav" data-i18n="nav.restore">恢复中心</button>
    <button data-page="nas" class="nav" data-i18n="nav.nas">NAS / Restic</button>
    <button data-page="migration" class="nav" data-i18n="nav.migration">Dataset 迁移</button>
    <button data-page="windows" class="nav" data-i18n="nav.windows">Windows 备份</button>
    <button data-page="cloud" class="nav" data-i18n="nav.cloud">云端副本</button>
    <button data-page="pve" class="nav" data-i18n="nav.pve">PVE / PBS</button>
    <button data-page="jobs" class="nav" data-i18n="nav.jobs">任务日志</button>
  </aside>
  <main class="main">
    <section id="login-page" class="login-page" style="display:none;"></section>
    <section id="workspace" class="page active"></section>
    <section id="overview" class="page"></section>
    <section id="devices" class="page"></section>
    <section id="resources" class="page"></section>
    <section id="operations" class="page"></section>
    <section id="tasks" class="page"></section>
    <section id="monitoring" class="page"></section>
    <section id="scheduler" class="page"></section>
    <section id="history" class="page"></section>
    <section id="storage" class="page"></section>
    <section id="restore" class="page"></section>
    <section id="nas" class="page"></section>
    <section id="migration" class="page"></section>
    <section id="windows" class="page"></section>
    <section id="cloud" class="page"></section>
    <section id="pve" class="page"></section>
    <section id="jobs" class="page"></section>
  </main>
  <div id="operationStatusRegion" class="operation-status-region" aria-live="polite"></div>
  <dialog id="dangerDialog">
    <form method="dialog" class="dialog-card">
      <h3 id="dangerTitle"></h3>
      <p id="dangerBody"></p>
      <pre id="dangerCommand"></pre>
      <label data-i18n="dialog.inputConfirm">输入确认文字
        <input id="dangerInput" autocomplete="off">
      </label>
      <div class="dialog-actions">
        <button value="cancel" class="secondary" data-i18n="btn.cancel">取消</button>
        <button value="confirm" class="danger" data-i18n="btn.confirm">确认执行</button>
      </div>
    </form>
  </dialog>
  <dialog id="skipDialog">
    <form method="dialog" class="dialog-card">
      <h3 id="skipTitle" data-i18n="dialog.skipTitle">暂时跳过此步骤</h3>
      <p data-i18n="dialog.skipDesc">说明原因后，此步骤会显示"已跳过"，之后可以随时重新启用。</p>
      <label for="skipReason" data-i18n="dialog.skipReason">跳过原因</label>
      <textarea id="skipReason" maxlength="200" data-i18n-placeholder="dialog.skipPlaceholder" placeholder="例如：当前没有需要备份的 Windows 电脑"></textarea>
      <div class="dialog-actions">
        <button value="cancel" class="secondary" data-i18n="btn.cancel">取消</button>
        <button value="confirm" data-i18n="dialog.confirmSkip">确认跳过</button>
      </div>
    </form>
  </dialog>
  <script src="/static/i18n.js"></script>
  <script src="/static/workflow.js"></script>
  <script src="/static/components/index.js"></script>
  <script src="/static/stores/index.js"></script>
  <script src="/static/workspace.js"></script>
  <script src="/static/device-registry.js"></script>
  <script src="/static/resource-registry.js"></script>
  <script src="/static/operation-engine.js"></script>
  <script src="/static/task-engine.js"></script>
  <script src="/static/monitoring-engine.js"></script>
  <script src="/static/scheduler-engine.js"></script>
  <script src="/static/history-engine.js"></script>
  <script src="/static/auth.js"></script>
  <script src="/static/app.js"></script>
</body>
</html>
"""
