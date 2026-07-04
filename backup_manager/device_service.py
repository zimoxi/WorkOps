"""DeviceService — business logic for Device CRUD."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from .device_repository import DeviceRepository


VALID_TYPES = {"windows", "linux", "omv", "pve", "pbs", "nas", "router", "other"}
VALID_STATUSES = {"online", "offline", "unknown"}

MOCK_DEVICES = [
    {"name": "Windows-PC", "type": "windows", "ip": "192.168.1.100", "status": "online", "description": "主工作站"},
    {"name": "Linux-Server", "type": "linux", "ip": "192.168.1.10", "status": "online", "description": "Ubuntu 服务器"},
    {"name": "OMV", "type": "omv", "ip": "192.168.1.5", "status": "online", "description": "OpenMediaVault NAS"},
    {"name": "PVE", "type": "pve", "ip": "192.168.1.3", "status": "online", "description": "Proxmox VE 宿主机"},
    {"name": "PBS", "type": "pbs", "ip": "192.168.1.4", "status": "offline", "description": "Proxmox Backup Server"},
    {"name": "NAS", "type": "nas", "ip": "192.168.1.2", "status": "online", "description": "群晖 NAS"},
    {"name": "Router", "type": "router", "ip": "192.168.1.1", "status": "online", "description": "主路由"},
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


class DeviceService:
    """Business logic layer for Device operations.

    All validation and business rules go here.
    Repository handles raw SQL only.
    """

    def __init__(self, repo: DeviceRepository) -> None:
        self._repo = repo

    def ensure_mock_data(self) -> int:
        """Insert mock devices if table is empty. Returns count inserted."""
        if self._repo.count() > 0:
            return 0
        now = _now_iso()
        for mock in MOCK_DEVICES:
            self._repo.insert({
                "id": _new_id(),
                "name": mock["name"],
                "type": mock["type"],
                "ip": mock["ip"],
                "status": mock["status"],
                "description": mock["description"],
                "created_at": now,
                "updated_at": now,
            })
        return len(MOCK_DEVICES)

    def list_devices(self) -> list[dict[str, Any]]:
        return self._repo.list_all()

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        return self._repo.get_by_id(device_id)

    def create_device(self, data: dict[str, Any]) -> dict[str, Any]:
        name = (data.get("name") or "").strip()
        dtype = (data.get("type") or "").strip().lower()
        if not name:
            raise ValueError("name is required")
        if dtype not in VALID_TYPES:
            raise ValueError(f"type must be one of: {', '.join(sorted(VALID_TYPES))}")

        status = (data.get("status") or "offline").strip().lower()
        if status not in VALID_STATUSES:
            status = "offline"

        now = _now_iso()
        device = {
            "id": _new_id(),
            "name": name,
            "type": dtype,
            "ip": (data.get("ip") or "").strip(),
            "status": status,
            "description": (data.get("description") or "").strip(),
            "created_at": now,
            "updated_at": now,
        }
        self._repo.insert(device)
        return device

    def update_device(self, device_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        existing = self._repo.get_by_id(device_id)
        if not existing:
            return None

        fields: dict[str, Any] = {}
        if "name" in data:
            name = (data["name"] or "").strip()
            if not name:
                raise ValueError("name cannot be empty")
            fields["name"] = name
        if "type" in data:
            dtype = (data["type"] or "").strip().lower()
            if dtype not in VALID_TYPES:
                raise ValueError(f"type must be one of: {', '.join(sorted(VALID_TYPES))}")
            fields["type"] = dtype
        if "ip" in data:
            fields["ip"] = (data["ip"] or "").strip()
        if "status" in data:
            status = (data["status"] or "").strip().lower()
            if status in VALID_STATUSES:
                fields["status"] = status
        if "description" in data:
            fields["description"] = (data["description"] or "").strip()

        if fields:
            fields["updated_at"] = _now_iso()
            self._repo.update(device_id, fields)

        return self._repo.get_by_id(device_id)

    def delete_device(self, device_id: str) -> bool:
        return self._repo.delete(device_id)
