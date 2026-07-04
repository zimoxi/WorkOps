from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable

from .restore_center import validate_staging_delete_path


class OperationError(ValueError):
    pass


@dataclass
class PreparedCommand:
    id: str
    title: str
    argv: list[str]
    env: list[str]
    danger: str
    instructions: str
    impact: str
    recovery: str
    confirm_text: str = ""
    cwd: str = ""


Builder = Callable[[dict], PreparedCommand]


def build_restic_environment(repository: str, password_file: str) -> list[str]:
    if not repository:
        raise OperationError("restic repository is required")
    if not password_file:
        raise OperationError("restic password file is required")
    return [
        f"RESTIC_REPOSITORY={repository}",
        f"RESTIC_PASSWORD_FILE={password_file}",
    ]


def validate_restore_target(target: str) -> str:
    if not target:
        raise OperationError("restore target is required")
    normalized = str(PurePosixPath(target))
    blocked = {"/", "/tmp", "/var", "/etc", "/root", "/usr", "/boot"}
    if normalized in blocked or normalized.startswith("/tmp/"):
        raise OperationError(
            "restore target points to a system or temporary path; choose a large data disk"
        )
    if not normalized.startswith("/"):
        raise OperationError("restore target must be an absolute Linux path")
    return normalized


def require_paths(paths: list[str], field_name: str) -> list[str]:
    clean = [path for path in paths if path]
    if not clean:
        raise OperationError(f"{field_name} must contain at least one path")
    return clean


class CommandCatalog:
    def __init__(self) -> None:
        self.builders: dict[str, Builder] = {
            "restic-snapshots": self._restic_snapshots,
            "restic-backup": self._restic_backup,
            "restic-check": self._restic_check,
            "restic-prune": self._restic_prune,
            "restic-restore": self._restic_restore,
            "restore-staging-delete": self._restore_staging_delete,
            "migration-create-temp": self._migration_create_temp,
            "migration-rsync": self._migration_rsync,
            "pve-list-guests": self._pve_list_guests,
            "pve-vzdump": self._pve_vzdump,
            "cloud-rclone-check": self._cloud_rclone_check,
            "cloud-rclone-list": self._cloud_rclone_list,
            "cloud-rclone-pull": self._cloud_rclone_pull,
            "cloud-rclone-sync": self._cloud_rclone_sync,
            "windows-robocopy-preview": self._windows_robocopy_preview,
        }

    def build(self, operation_id: str, payload: dict) -> PreparedCommand:
        builder = self.builders.get(operation_id)
        if builder is None:
            raise OperationError(f"operation is not allowed: {operation_id}")
        return builder(payload)

    def operations(self) -> list[dict[str, str]]:
        return [
            {"id": operation_id, "title": operation_id.replace("-", " ").title()}
            for operation_id in sorted(self.builders)
        ]

    def _restic_snapshots(self, payload: dict) -> PreparedCommand:
        env = build_restic_environment(
            payload.get("repository", ""), payload.get("password_file", "")
        )
        return PreparedCommand(
            id="restic-snapshots",
            title="List Restic snapshots",
            argv=["restic", "snapshots"],
            env=env,
            danger="low",
            instructions="Read the snapshot list from the Restic repository.",
            impact="Read-only operation.",
            recovery="Check the repository path and password file if the command fails.",
        )

    def _restic_backup(self, payload: dict) -> PreparedCommand:
        env = build_restic_environment(
            payload.get("repository", ""), payload.get("password_file", "")
        )
        include_paths = require_paths(payload.get("include_paths", []), "include_paths")
        argv = ["restic", "backup", *include_paths]
        exclude_file = payload.get("exclude_file", "")
        if exclude_file:
            argv.extend(["--exclude-file", exclude_file])
        exclude_patterns = [
            str(item).strip() for item in payload.get("exclude_patterns", []) if str(item).strip()
        ]
        for pattern in exclude_patterns:
            argv.extend(["--exclude", pattern])
        tag = payload.get("tag", "")
        if tag:
            argv.extend(["--tag", tag])
        return PreparedCommand(
            id="restic-backup",
            title="Run Restic backup",
            argv=argv,
            env=env,
            danger="medium",
            instructions="Write a new backup snapshot into the Restic repository.",
            impact="Reads source folders and writes a new snapshot to the repository.",
            recovery="Check repository access, password file, and source paths if the backup fails.",
        )

    def _restic_check(self, payload: dict) -> PreparedCommand:
        env = build_restic_environment(
            payload.get("repository", ""), payload.get("password_file", "")
        )
        return PreparedCommand(
            id="restic-check",
            title="Check Restic repository",
            argv=["restic", "check"],
            env=env,
            danger="low",
            instructions="Verify Restic repository integrity.",
            impact="Read-only repository verification.",
            recovery="Stop prune and cloud sync until repository errors are reviewed.",
        )

    def _restic_prune(self, payload: dict) -> PreparedCommand:
        env = build_restic_environment(
            payload.get("repository", ""), payload.get("password_file", "")
        )
        argv = [
            "restic",
            "forget",
            "--keep-daily",
            str(payload.get("keep_daily", 30)),
            "--keep-weekly",
            str(payload.get("keep_weekly", 12)),
            "--keep-monthly",
            str(payload.get("keep_monthly", 24)),
            "--prune",
        ]
        return PreparedCommand(
            id="restic-prune",
            title="Prune Restic snapshots",
            argv=argv,
            env=env,
            danger="high",
            instructions="Delete snapshots outside the retention policy and reclaim repository space.",
            impact="Old snapshots will be deleted from the repository.",
            recovery="Review recent snapshots before pruning; deleted snapshots usually cannot be recovered from the same repository.",
            confirm_text="I understand the retention policy",
        )

    def _restic_restore(self, payload: dict) -> PreparedCommand:
        env = build_restic_environment(
            payload.get("repository", ""), payload.get("password_file", "")
        )
        target = validate_restore_target(payload.get("target", ""))
        snapshot = payload.get("snapshot", "latest")
        paths = payload.get("paths", [])
        argv = ["restic", "restore", snapshot, "--target", target]
        for path in paths:
            if path:
                argv.extend(["--path", path])
        return PreparedCommand(
            id="restic-restore",
            title="Restore Restic data",
            argv=argv,
            env=env,
            danger="high",
            instructions="Restore backup data to the selected target directory.",
            impact="Large amounts of data may be written into the restore target.",
            recovery="Use a larger data path if the restore target runs out of space; do not use /tmp.",
            confirm_text="I confirm the restore target is not a system path",
        )

    def _restore_staging_delete(self, payload: dict) -> PreparedCommand:
        root_path = validate_restore_target(payload.get("root_path", ""))
        target = validate_restore_target(payload.get("target", ""))
        target = validate_staging_delete_path(root_path, target)
        confirm_text = payload.get("confirm_text", "").strip()
        if not confirm_text:
            raise OperationError("confirm_text is required")
        return PreparedCommand(
            id="restore-staging-delete",
            title="Delete restore staging directory",
            argv=["rm", "-rf", target],
            env=[],
            danger="high",
            instructions="Delete one restore staging directory inside the configured restore root.",
            impact="All files in the selected staging directory will be permanently removed.",
            recovery="Recover the data again from the backup repository if a staging directory is deleted by mistake.",
            confirm_text=confirm_text,
        )

    def _migration_create_temp(self, payload: dict) -> PreparedCommand:
        mountpoint = payload.get("mountpoint", "")
        name = payload.get("name", "_migration")
        if not mountpoint.startswith("/"):
            raise OperationError("mountpoint must be an absolute Linux path")
        target = f"{mountpoint.rstrip('/')}/{name}"
        return PreparedCommand(
            id="migration-create-temp",
            title="Create migration temp directory",
            argv=["mkdir", "-p", target],
            env=[],
            danger="medium",
            instructions="Create a temporary migration directory on the same data pool.",
            impact="Creates a directory but does not move data yet.",
            recovery="Delete the temporary directory later if it is no longer needed.",
        )

    def _migration_rsync(self, payload: dict) -> PreparedCommand:
        source = payload.get("source", "")
        target = payload.get("target", "")
        if not source.startswith("/") or not target.startswith("/"):
            raise OperationError("source and target must be absolute Linux paths")
        return PreparedCommand(
            id="migration-rsync",
            title="Copy data into new dataset",
            argv=[
                "rsync",
                "-aHAX",
                "--numeric-ids",
                "--info=progress2",
                f"{source.rstrip('/')}/",
                f"{target.rstrip('/')}/",
            ],
            env=[],
            danger="high",
            instructions="Copy data from the old directory into the new dataset mountpoint.",
            impact="Large data copy operation that may temporarily consume double space.",
            recovery="Keep the original directory until verification is complete; rerun rsync after fixing space or permissions issues.",
            confirm_text="I confirm the source remains intact and the target has enough space",
        )

    def _pve_list_guests(self, payload: dict) -> PreparedCommand:
        return PreparedCommand(
            id="pve-list-guests",
            title="List PVE guests",
            argv=["sh", "-lc", "qm list && pct list && pvesm status"],
            env=[],
            danger="low",
            instructions="Read PVE VM, CT, and storage state from the host.",
            impact="Read-only operation.",
            recovery="Run this on the PVE host or through SSH to the PVE host.",
        )

    def _pve_vzdump(self, payload: dict) -> PreparedCommand:
        guest_id = str(payload.get("guest_id", "")).strip()
        storage = payload.get("storage", "")
        if not guest_id.isdigit():
            raise OperationError("guest_id must be a VM/CT numeric id")
        if not storage:
            raise OperationError("PBS storage id is required")
        return PreparedCommand(
            id="pve-vzdump",
            title="Backup PVE guest to PBS",
            argv=[
                "vzdump",
                guest_id,
                "--storage",
                storage,
                "--mode",
                payload.get("mode", "snapshot"),
            ],
            env=[],
            danger="medium",
            instructions="Run native PVE backup to the configured PBS storage.",
            impact="Creates a backup task and consumes disk and network IO.",
            recovery="Check the PVE task log and PBS storage connectivity if the job fails.",
        )

    def _cloud_rclone_sync(self, payload: dict) -> PreparedCommand:
        source = payload.get("source", "")
        remote = payload.get("remote", "")
        if not source or not remote:
            raise OperationError("source and remote are required")
        return PreparedCommand(
            id="cloud-rclone-sync",
            title="Sync encrypted repository to cloud",
            argv=["rclone", "sync", source, remote, "--progress"],
            env=[],
            danger="medium",
            instructions="Sync the encrypted Restic repository to cloud storage.",
            impact="Remote files may be uploaded, updated, or deleted to match the source.",
            recovery="Run a dry-run manually before the first full sync if you are unsure about direction.",
            confirm_text="I confirm the sync direction is correct",
        )

    def _cloud_rclone_check(self, payload: dict) -> PreparedCommand:
        remote = payload.get("remote", "")
        if not remote:
            raise OperationError("remote is required")
        return PreparedCommand(
            id="cloud-rclone-check",
            title="Validate cloud remote",
            argv=["rclone", "lsd", remote],
            env=[],
            danger="low",
            instructions="List the remote directory before running the full cloud sync.",
            impact="Read-only validation against the configured remote target.",
            recovery="Check the remote definition, endpoint, account, and path if the listing fails.",
        )

    def _cloud_rclone_list(self, payload: dict) -> PreparedCommand:
        remote = payload.get("remote", "")
        if not remote:
            raise OperationError("remote is required")
        return PreparedCommand(
            id="cloud-rclone-list",
            title="List remote repository contents",
            argv=["rclone", "lsf", remote],
            env=[],
            danger="low",
            instructions="List files and directories inside the cloud repository path.",
            impact="Read-only listing against the configured remote path.",
            recovery="Check the remote path or run remote validation first if listing fails.",
        )

    def _cloud_rclone_pull(self, payload: dict) -> PreparedCommand:
        remote = payload.get("remote", "")
        target = validate_restore_target(payload.get("target", ""))
        if not remote:
            raise OperationError("remote is required")
        return PreparedCommand(
            id="cloud-rclone-pull",
            title="Copy encrypted repository down from cloud",
            argv=["rclone", "copy", remote, target, "--progress"],
            env=[],
            danger="medium",
            instructions="Copy the encrypted cloud repository into a local recovery directory.",
            impact="Writes repository files into the selected local recovery path without deleting the cloud source.",
            recovery="Choose a larger local path or clear the target directory if the copy fails due to space or conflicts.",
            confirm_text="I confirm the local cloud restore path has enough space",
        )

    def _windows_robocopy_preview(self, payload: dict) -> PreparedCommand:
        source = str(payload.get("source") or payload.get("drive") or "").strip()
        target = str(payload.get("target", "")).rstrip("\\/")
        if len(source) == 1 and source.isalpha():
            source = f"{source.upper()}:\\"
        elif len(source) == 2 and source[0].isalpha() and source[1] == ":":
            source = f"{source.upper()}\\"
        if (
            len(source) < 3
            or not source[0].isalpha()
            or source[1] != ":"
            or source[2] not in "\\/"
        ):
            raise OperationError("source must be an absolute Windows drive or folder path")
        if not target:
            raise OperationError("SMB target is required")
        normalized = source.rstrip("\\/").replace(":", "")
        destination_name = normalized.replace("\\", "-").replace("/", "-")
        destination_name = destination_name or source[0].upper()
        return PreparedCommand(
            id="windows-robocopy-preview",
            title="Generate Windows backup command",
            argv=[
                "robocopy",
                source,
                f"{target}\\{destination_name}",
                "/MIR",
                "/XJ",
                "/R:2",
                "/W:5",
                "/Z",
                "/MT:16",
                "/COPY:DAT",
                "/DCOPY:DAT",
            ],
            env=[],
            danger="medium",
            instructions="Preview the robocopy command that mirrors a Windows drive or folder to NAS.",
            impact="Mirror mode may delete destination-only files.",
            recovery="Remove /MIR for the first run or point the command to an empty destination folder.",
            confirm_text="I confirm the robocopy destination is correct",
        )
