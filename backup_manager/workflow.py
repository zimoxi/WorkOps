from __future__ import annotations

from typing import Any, Iterable

from .config import AppConfig


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

SUCCESS_OPERATIONS = {
    "first_backup": "restic-backup",
    "restore_center": "restic-restore",
    "pve_pbs": "pve-vzdump",
}


def derive_workflow(
    config: AppConfig,
    jobs: Iterable[Any],
    runtime: dict[str, object] | None = None,
) -> dict[str, Any]:
    job_list = list(jobs)
    runtime = runtime or {}
    steps = []
    for step_id, title, optional in STEP_DEFINITIONS:
        status, completed_at = derive_step_status(step_id, config, job_list, runtime)
        skip_reason = config.workflow.skipped_steps.get(step_id, "")
        if optional and status not in {"complete", "unavailable"} and skip_reason:
            status = "skipped"
        steps.append(
            {
                "id": step_id,
                "title": title,
                "optional": optional,
                "status": status,
                "skip_reason": skip_reason if status == "skipped" else "",
                "completed_at": completed_at,
            }
        )

    next_step = next(
        (
            step["id"]
            for step in steps
            if step["status"] not in {"complete", "skipped", "unavailable"}
        ),
        "",
    )
    completed_count = sum(
        step["status"] in {"complete", "skipped", "unavailable"} for step in steps
    )
    return {
        "steps": steps,
        "next_step": next_step,
        "completed_count": completed_count,
        "total_count": len(steps),
        "is_complete": not next_step,
    }


def derive_step_status(
    step_id: str,
    config: AppConfig,
    jobs: list[Any],
    runtime: dict[str, object],
) -> tuple[str, str]:
    if step_id == "connect":
        ssh_test = config.workflow.completed_at.get("ssh_test", "")
        discovery = config.workflow.completed_at.get("storage_discovery", "")
        if ssh_test and discovery:
            return "complete", max(ssh_test, discovery)
        if ssh_test or discovery or config.ssh_host:
            return "needs_attention", ""
        return "not_started", ""

    if step_id == "storage":
        if config.active_storage():
            return "complete", config.workflow.completed_at.get("storage", "")
        if config.storage_targets:
            return "needs_attention", ""
        return "not_started", ""

    if step_id == "restore_root":
        configured = bool(config.restore_roots and config.active_restore_root())
        if configured:
            return "complete", config.workflow.completed_at.get("restore_root", "")
        return "not_started", ""

    if step_id == "dataset":
        completed_at = config.workflow.completed_at.get("dataset", "")
        return ("complete", completed_at) if completed_at else ("not_started", "")

    if step_id == "restic":
        has_paths = any(item.include_paths for item in config.backup_sets)
        configured = bool(
            config.restic.repository and config.restic.password_file and has_paths
        )
        if configured:
            return "complete", config.workflow.completed_at.get("restic", "")
        if config.restic.repository or config.restic.password_file or config.backup_sets:
            return "needs_attention", ""
        return "not_started", ""

    if step_id in SUCCESS_OPERATIONS:
        finished_at = latest_success_time(jobs, SUCCESS_OPERATIONS[step_id])
        return ("complete", finished_at) if finished_at else ("not_started", "")

    if step_id == "schedule":
        completed_at = config.workflow.completed_at.get("schedule", "")
        return ("complete", completed_at) if completed_at else ("not_started", "")

    if step_id == "windows":
        if runtime.get("local_platform") != "windows":
            return "unavailable", ""
        windows = config.windows_backup
        configured = bool(
            windows.enabled and windows.source_drives and windows.smb_target
        )
        if configured:
            return "complete", config.workflow.completed_at.get("windows", "")
        if windows.enabled or windows.smb_target:
            return "needs_attention", ""
        return "not_started", ""

    if step_id == "cloud":
        if not config.cloud_remote.enabled and not config.cloud_remote.remote_name:
            return "not_started", ""
        finished_at = latest_success_time(jobs, "cloud-rclone-sync")
        verified_at = str(config.cloud_remote.verified_at or "").strip()
        completed_at = max(
            [item for item in (finished_at, verified_at) if item],
            default="",
        )
        return ("complete", completed_at) if completed_at else ("needs_attention", "")

    if step_id == "pve_pbs":
        if runtime.get("host_platform") not in {"pve"}:
            return "unavailable", ""
        if not config.pve_pbs.enabled and not config.pve_pbs.pbs_storage:
            return "not_started", ""
        finished_at = latest_success_time(jobs, SUCCESS_OPERATIONS["pve_pbs"])
        return ("complete", finished_at) if finished_at else ("needs_attention", "")

    return "not_started", ""


def latest_success_time(jobs: list[Any], operation_id: str) -> str:
    matches = []
    for job in jobs:
        if job_value(job, "operation_id") != operation_id:
            continue
        if job_value(job, "status") != "success":
            continue
        matches.append(str(job_value(job, "finished_at") or ""))
    return max(matches, default="")


def job_value(job: Any, key: str) -> Any:
    if isinstance(job, dict):
        return job.get(key)
    return getattr(job, key, None)
