from __future__ import annotations


def detect_local_platform(system_name: str | None = None) -> dict[str, object]:
    normalized = (system_name or "").strip().lower()
    if normalized == "windows":
        return {"kind": "windows-local", "label": "Windows Local", "source": "local"}
    return {"kind": "linux", "label": "Linux", "source": "local"}


def detect_remote_platform(command_presence: dict[str, bool]) -> dict[str, object]:
    if all(
        command_presence.get(name, False)
        for name in ("pveversion", "qm", "pct", "pvesm")
    ):
        return {"kind": "pve", "label": "Proxmox VE", "source": "remote"}
    if command_presence.get("omv-confdbadm", False):
        return {"kind": "omv", "label": "OpenMediaVault", "source": "remote"}
    return {"kind": "linux", "label": "Linux", "source": "remote"}


def detect_remote_capabilities(command_presence: dict[str, bool]) -> dict[str, bool]:
    return {
        "zfs": command_presence.get("zpool", False)
        and command_presence.get("zfs", False),
        "restic": command_presence.get("restic", False),
        "rclone": command_presence.get("rclone", False),
        "systemd": command_presence.get("systemctl", False),
        "cron": command_presence.get("crontab", False),
        "pbs": command_presence.get("proxmox-backup-client", False)
        or command_presence.get("pvesm", False),
        "smb": command_presence.get("smbstatus", False)
        or command_presence.get("mount.cifs", False),
    }
