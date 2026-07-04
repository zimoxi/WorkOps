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
            "windows_drives": discovery.get("windows_drives", []),
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
                "source_system": "storage",
                "destination": restic["repository"],
                "schedule_source": "config",
                "latest_execution_time": latest_job_time(jobs, "restic-backup"),
                "latest_result": latest_job_status(jobs, "restic-backup"),
                "origin": "app_managed",
                "next_step": "restore_center",
            }
        )
    windows = config.get("windows_backup", {})
    if windows.get("enabled") and windows.get("smb_target"):
        rows.append(
            {
                "name": "Windows Local Backup",
                "type": "windows_local",
                "source_system": "windows-local",
                "destination": windows["smb_target"],
                "schedule_source": "config",
                "latest_execution_time": latest_job_time(
                    jobs, "windows-robocopy-preview"
                ),
                "latest_result": latest_job_status(jobs, "windows-robocopy-preview"),
                "origin": "app_managed",
                "next_step": "windows",
            }
        )
    cloud = config.get("cloud_remote", {})
    if cloud.get("enabled") and cloud.get("remote_name"):
        destination = cloud_destination(cloud)
        rows.append(
            {
                "name": "Cloud Copy",
                "type": "cloud",
                "source_system": "storage",
                "destination": destination,
                "schedule_source": "config",
                "latest_execution_time": latest_job_time(jobs, "cloud-rclone-sync"),
                "latest_result": latest_job_status(jobs, "cloud-rclone-sync"),
                "verified_at": str(cloud.get("verified_at", "")),
                "verification_target": cloud_verification_target(cloud),
                "latest_check_time": latest_job_time(jobs, "cloud-rclone-check"),
                "latest_check_result": latest_job_status(jobs, "cloud-rclone-check"),
                "origin": "app_managed",
                "next_step": "cloud",
            }
        )
    pve = config.get("pve_pbs", {})
    if pve.get("enabled") and pve.get("pbs_storage"):
        rows.append(
            {
                "name": "PVE / PBS",
                "type": "pve_pbs",
                "source_system": pve.get("pve_host", "pve"),
                "destination": pve["pbs_storage"],
                "schedule_source": "config",
                "latest_execution_time": latest_job_time(jobs, "pve-vzdump"),
                "latest_result": latest_job_status(jobs, "pve-vzdump"),
                "origin": "app_managed",
                "next_step": "pve_pbs",
            }
        )
    return rows


def summarize_backup_artifacts(discovery: dict) -> list[dict]:
    return list(discovery.get("restic_snapshots", [])) + list(
        discovery.get("pbs_backups", [])
    )


def summarize_warnings(schedules: list[dict], restore_center: dict) -> list[dict]:
    warnings: list[dict] = []
    commands: dict[str, list[str]] = {}
    for item in schedules:
        command = str(item.get("command", "")).strip()
        if not command:
            continue
        commands.setdefault(command, []).append(str(item.get("id", "")))
    for command, ids in commands.items():
        if len(ids) > 1:
            warnings.append(
                {
                    "code": "duplicate_schedule",
                    "message": command,
                    "related_ids": ids,
                }
            )
    if any(
        row.get("status") == "cleanup_pending"
        for row in restore_center.get("app_managed", [])
    ):
        warnings.append(
            {
                "code": "staging_cleanup_pending",
                "message": "Restore staging cleanup is pending",
            }
        )
    return warnings


def cloud_destination(cloud: dict) -> str:
    remote_name = str(cloud.get("remote_name", "")).strip()
    remote_path = str(cloud.get("remote_path", "")).strip().lstrip("/")
    if not remote_name:
        return ""
    if ":" in remote_name and not remote_path:
        return remote_name
    if remote_path:
        return f"{remote_name}:{remote_path}"
    return f"{remote_name}:"


def cloud_verification_target(cloud: dict) -> str:
    remote_name = str(cloud.get("remote_name", "")).strip()
    verify_path = str(cloud.get("verify_path", "")).strip().lstrip("/")
    if not remote_name:
        return ""
    if verify_path:
        return f"{remote_name}:{verify_path}"
    return f"{remote_name}:"


def latest_job_status(jobs: list[dict], operation_id: str) -> str:
    for job in jobs:
        if job.get("operation_id") == operation_id:
            return str(job.get("status", "unknown"))
    return "not_run"


def latest_job_time(jobs: list[dict], operation_id: str) -> str:
    for job in jobs:
        if job.get("operation_id") == operation_id:
            return str(job.get("finished_at", ""))
    return ""
