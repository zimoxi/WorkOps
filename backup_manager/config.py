from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


CLOUD_VERIFICATION_FIELDS = (
    "provider",
    "backend_type",
    "vendor",
    "remote_name",
    "remote_path",
    "endpoint",
    "region",
    "bucket",
    "username",
    "verify_path",
)


@dataclass
class StorageTarget:
    id: str
    name: str
    kind: str
    mountpoint: str
    pool_name: str = ""
    notes: str = ""


@dataclass
class RestoreRoot:
    id: str
    label: str
    path: str
    kind: str = "directory"
    app_managed: bool = False


@dataclass
class ResticRepo:
    repository: str = ""
    password_file: str = ""
    retention_daily: int = 30
    retention_weekly: int = 12
    retention_monthly: int = 24


@dataclass
class BackupSet:
    id: str
    name: str
    include_paths: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)
    tag: str = "important"


@dataclass
class WindowsBackup:
    enabled: bool = False
    source_drives: list[str] = field(default_factory=lambda: ["D", "E"])
    smb_target: str = ""
    log_path: str = "C:\\Logs\\windows-drive-backup.log"


@dataclass
class CloudRemote:
    enabled: bool = False
    provider: str = "baidu"
    remote_name: str = ""
    remote_path: str = ""
    sync_source: str = ""
    backend_type: str = ""
    vendor: str = ""
    endpoint: str = ""
    region: str = ""
    bucket: str = ""
    username: str = ""
    verify_path: str = ""
    guide_id: str = ""
    guide_url: str = ""
    verified_at: str = ""
    notes: str = ""


@dataclass
class PvePbsConfig:
    enabled: bool = False
    pve_host: str = ""
    pbs_storage: str = ""
    target_version: str = ""
    selected_guests: list[str] = field(default_factory=list)


@dataclass
class WorkflowConfig:
    skipped_steps: dict[str, str] = field(default_factory=dict)
    completed_at: dict[str, str] = field(default_factory=dict)


@dataclass
class AppConfig:
    executor_mode: str = "mock"
    ssh_host: str = ""
    ssh_user: str = "root"
    ssh_port: int = 22
    ssh_auth_mode: str = "ssh_config"
    ssh_key_path: str = ""
    storage_targets: list[StorageTarget] = field(default_factory=list)
    active_storage_id: str = ""
    active_restore_root_id: str = ""
    restic: ResticRepo = field(default_factory=ResticRepo)
    backup_sets: list[BackupSet] = field(default_factory=list)
    windows_backup: WindowsBackup = field(default_factory=WindowsBackup)
    cloud_remote: CloudRemote = field(default_factory=CloudRemote)
    pve_pbs: PvePbsConfig = field(default_factory=PvePbsConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    migration_root_name: str = "_migration"
    restore_roots: list[RestoreRoot] = field(default_factory=list)
    platform_override: str = ""
    notification_emails: list[str] = field(default_factory=list)
    notification_sender: str = ""

    @classmethod
    def default(cls) -> "AppConfig":
        return cls()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        return cls(
            executor_mode=data.get("executor_mode", "mock"),
            ssh_host=data.get("ssh_host", ""),
            ssh_user=data.get("ssh_user", "root"),
            ssh_port=int(data.get("ssh_port", 22)),
            ssh_auth_mode=data.get("ssh_auth_mode", "ssh_config"),
            ssh_key_path=data.get("ssh_key_path", ""),
            storage_targets=[
                StorageTarget(**item) for item in data.get("storage_targets", [])
            ],
            active_storage_id=data.get("active_storage_id", ""),
            active_restore_root_id=data.get("active_restore_root_id", ""),
            restic=ResticRepo(**data.get("restic", {})),
            backup_sets=[BackupSet(**item) for item in data.get("backup_sets", [])],
            windows_backup=WindowsBackup(**data.get("windows_backup", {})),
            cloud_remote=CloudRemote(**data.get("cloud_remote", {})),
            pve_pbs=PvePbsConfig(**data.get("pve_pbs", {})),
            workflow=WorkflowConfig(**data.get("workflow", {})),
            migration_root_name=data.get("migration_root_name", "_migration"),
            restore_roots=[
                RestoreRoot(**item) for item in data.get("restore_roots", [])
            ],
            platform_override=data.get("platform_override", ""),
            notification_emails=list(data.get("notification_emails", [])),
            notification_sender=data.get("notification_sender", ""),
        )

    @classmethod
    def from_json(cls, text: str) -> "AppConfig":
        return cls.from_dict(json.loads(text))

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)

    def active_storage(self) -> StorageTarget | None:
        for target in self.storage_targets:
            if target.id == self.active_storage_id:
                return target
        return self.storage_targets[0] if self.storage_targets else None

    def active_restore_root(self) -> RestoreRoot | None:
        for root in self.restore_roots:
            if root.id == self.active_restore_root_id:
                return root
        return self.restore_roots[0] if self.restore_roots else None


class ConfigStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> AppConfig:
        if not self.path.exists():
            return AppConfig.default()
        return AppConfig.from_json(self.path.read_text(encoding="utf-8"))

    def save(self, config: AppConfig) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(config.to_json(), encoding="utf-8")

    def update(self, patch: dict[str, Any]) -> AppConfig:
        current = self.load()
        data = current.to_dict()
        deep_merge(data, patch)
        normalize_cloud_remote(data.get("cloud_remote", {}), current.to_dict().get("cloud_remote", {}))
        config = AppConfig.from_dict(data)
        self.save(config)
        return config


def deep_merge(target: dict[str, Any], patch: dict[str, Any]) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value


def normalize_cloud_remote(current: dict[str, Any], previous: dict[str, Any]) -> None:
    if not isinstance(current, dict):
        return

    for key in ("remote_name", "remote_path", "verify_path", "provider", "backend_type", "vendor", "endpoint", "region", "bucket", "username"):
        if key in current and current[key] is not None:
            current[key] = str(current[key]).strip()
    for key in ("remote_path", "verify_path"):
        if key in current:
            current[key] = str(current[key]).lstrip("/")

    changed = any(
        str(previous.get(field, "")).strip() != str(current.get(field, "")).strip()
        for field in CLOUD_VERIFICATION_FIELDS
    )
    if changed or not str(current.get("remote_name", "")).strip():
        current["verified_at"] = ""
