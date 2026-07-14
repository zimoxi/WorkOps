"""DeviceRepository — SQLite CRUD for device table."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class DeviceRepository:
    """Low-level SQLite access for the device table.

    This class contains NO business logic.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._ensure_table()

    @contextmanager
    def _connect(self):
        """Context manager that opens and CLOSES the connection."""
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def close(self) -> None:
        """No-op for compatibility. Connections are closed per-operation."""
        pass

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS device (
                    id          TEXT PRIMARY KEY,
                    name        TEXT NOT NULL,
                    type        TEXT NOT NULL,
                    ip          TEXT DEFAULT '',
                    status      TEXT DEFAULT 'offline',
                    description TEXT DEFAULT '',
                    created_at  TEXT NOT NULL,
                    updated_at  TEXT NOT NULL
                )
            """)
            conn.commit()

    def list_all(self) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM device ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_by_id(self, device_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM device WHERE id = ?", (device_id,)
            ).fetchone()
            return dict(row) if row else None

    def insert(self, device: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO device (id, name, type, ip, status, description, created_at, updated_at)
                   VALUES (:id, :name, :type, :ip, :status, :description, :created_at, :updated_at)""",
                device,
            )
            conn.commit()

    def update(self, device_id: str, fields: dict[str, Any]) -> bool:
        if not fields:
            return False
        set_clause = ", ".join(f"{k} = :{k}" for k in fields)
        fields["id"] = device_id
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE device SET {set_clause} WHERE id = :id", fields
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, device_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM device WHERE id = ?", (device_id,)
            )
            conn.commit()
            return cursor.rowcount > 0

    def count(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) as cnt FROM device").fetchone()
            return row["cnt"] if row else 0
