"""
WorkOps Migration Runner — 数据库迁移
Sprint020: Persistence Foundation

显式调用，不自动运行
schema_version 管理
downgrade 全路径预检查
"""

import sqlite3
from datetime import datetime
from pathlib import Path

from .connection import connect
from .errors import (
    MigrationError,
    MigrationSafetyError,
    SchemaConflictError,
)


# ─── Managed Tables ────────────────────────────────

MANAGED_TABLES = {"tasks", "execution_results"}

MIGRATIONS = [
    (1, "create_tasks", """
        CREATE TABLE tasks (
            id              TEXT PRIMARY KEY,
            operation_id    TEXT NOT NULL DEFAULT '',
            operation_name  TEXT NOT NULL DEFAULT '',
            device_id       TEXT NOT NULL DEFAULT '',
            status          TEXT NOT NULL DEFAULT 'pending'
                            CHECK (status IN ('pending', 'running', 'success', 'failed', 'cancelled')),
            start_time      TEXT NOT NULL DEFAULT '',
            end_time        TEXT NOT NULL DEFAULT '',
            duration        TEXT NOT NULL DEFAULT ''
        )
    """),
    (2, "create_execution_results", """
        CREATE TABLE execution_results (
            task_id     TEXT PRIMARY KEY,
            status      TEXT NOT NULL DEFAULT ''
                        CHECK (status IN ('success', 'failed')),
            started_at  TEXT NOT NULL DEFAULT '',
            finished_at TEXT NOT NULL DEFAULT '',
            duration    TEXT NOT NULL DEFAULT '',
            stdout      TEXT NOT NULL DEFAULT '',
            stderr      TEXT NOT NULL DEFAULT '',
            exit_code   INTEGER NOT NULL DEFAULT 0,
            message     TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE RESTRICT
        )
    """),
]


class MigrationRunner:
    """Migration Runner"""

    def __init__(self, db_path):
        self._db_path = db_path

    def latest_version(self) -> int:
        """返回最新 Migration 版本号"""
        return len(MIGRATIONS)

    def current_version(self) -> int:
        """
        获取当前 schema 版本。
        
        - 数据库文件不存在时返回 0
        - schema_version 表不存在时返回 0
        - 只读，无写入副作用
        """
        if not Path(self._db_path).exists():
            return 0

        with connect(self._db_path) as conn:
            # 检查 schema_version 表是否存在
            row = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ).fetchone()
            if row is None:
                return 0

            row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
            return row[0] if row and row[0] is not None else 0

    def validate_schema(self) -> None:
        """
        验证 Schema 一致性。
        
        检测并拒绝：
        - 版本记录不连续
        - 存在未知未来版本
        - 版本已登记但对应表不存在
        - 托管表存在但版本未登记
        - schema_version 表结构错误
        """
        if not Path(self._db_path).exists():
            return

        with connect(self._db_path) as conn:
            # 检查 schema_version 表是否存在
            sv_table = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
            ).fetchone()

            if sv_table is None:
                # schema_version 不存在，检查是否有托管表
                for table_name in MANAGED_TABLES:
                    table = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,)
                    ).fetchone()
                    if table is not None:
                        raise SchemaConflictError(
                            f"Managed table '{table_name}' exists but schema_version table is missing"
                        )
                return

            # 检查 schema_version 表结构
            columns = {row[1] for row in conn.execute("PRAGMA table_info(schema_version)").fetchall()}
            required_columns = {"version", "name", "applied_at"}
            if not required_columns.issubset(columns):
                raise SchemaConflictError("schema_version table has incorrect structure")

            # 获取已登记版本
            rows = conn.execute("SELECT version, name FROM schema_version ORDER BY version").fetchall()
            registered_versions = {row[0]: row[1] for row in rows}

            # 检查版本连续性
            if registered_versions:
                versions = sorted(registered_versions.keys())
                for i, v in enumerate(versions):
                    if i == 0 and v != 1:
                        raise SchemaConflictError(f"Version sequence must start at 1, got {v}")
                    if i > 0 and v != versions[i - 1] + 1:
                        raise SchemaConflictError(f"Version gap: {versions[i-1]} -> {v}")

            # 检查未知未来版本
            max_migration = len(MIGRATIONS)
            for v in registered_versions:
                if v > max_migration:
                    raise SchemaConflictError(f"Unknown future version: {v}")

            # 检查版本已登记但对应表不存在
            for v, name in registered_versions.items():
                migration = MIGRATIONS[v - 1]
                table_name = self._extract_table_name(migration[2])
                if table_name:
                    table = conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                        (table_name,)
                    ).fetchone()
                    if table is None:
                        raise SchemaConflictError(
                            f"Version {v} registered but table '{table_name}' does not exist"
                        )

            # 检查托管表存在但版本未登记
            for table_name in MANAGED_TABLES:
                table = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                    (table_name,)
                ).fetchone()
                if table is not None:
                    # 检查是否在已登记版本中
                    found = False
                    for v, name in registered_versions.items():
                        migration = MIGRATIONS[v - 1]
                        if self._extract_table_name(migration[2]) == table_name:
                            found = True
                            break
                    if not found:
                        raise SchemaConflictError(
                            f"Managed table '{table_name}' exists but no version is registered"
                        )

    def upgrade(self, target_version=None) -> None:
        """
        升级到目标版本。
        
        - 显式调用
        - 空数据库初始化
        - 已有数据库升级
        - 重复运行安全
        - 事务失败 rollback
        """
        if target_version is None:
            target_version = len(MIGRATIONS)

        if target_version < 0 or target_version > len(MIGRATIONS):
            raise MigrationError(f"Invalid target version: {target_version}")

        current = self.current_version()

        if current == target_version:
            return  # 已经是目标版本

        if current > target_version:
            raise MigrationError(f"Current version {current} is higher than target {target_version}")

        # 确保 schema_version 表存在
        self._ensure_schema_version_table()

        # 执行升级
        with connect(self._db_path) as conn:
            for version, name, sql in MIGRATIONS:
                if version <= current:
                    continue
                if version > target_version:
                    break

                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_version (version, name, applied_at) VALUES (?, ?, ?)",
                    (version, name, datetime.now().isoformat())
                )

    def downgrade(self, target_version) -> None:
        """
        降级到目标版本。
        
        - 全路径预检查
        - 有数据时抛出 MigrationSafetyError
        - 同一事务中逐版本降级
        - 不得修改 device 表
        """
        if target_version < 0:
            raise MigrationError(f"Invalid target version: {target_version}")

        current = self.current_version()

        if current == target_version:
            return  # 已经是目标版本

        if current < target_version:
            raise MigrationError(f"Current version {current} is lower than target {target_version}")

        if not Path(self._db_path).exists():
            return

        # 全路径预检查
        with connect(self._db_path) as conn:
            for version, name, sql in reversed(MIGRATIONS):
                if version <= target_version:
                    break
                if version > current:
                    continue

                # 提取表名
                table_name = self._extract_table_name(sql)
                if table_name:
                    # 检查表是否有数据
                    row = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                    if row and row[0] > 0:
                        raise MigrationSafetyError(
                            f"Cannot downgrade from version {version}: table '{table_name}' has {row[0]} rows"
                        )

        # 预检查通过，执行降级
        with connect(self._db_path) as conn:
            for version, name, sql in reversed(MIGRATIONS):
                if version <= target_version:
                    break
                if version > current:
                    continue

                table_name = self._extract_table_name(sql)
                if table_name:
                    conn.execute(f"DROP TABLE IF EXISTS {table_name}")

                conn.execute(
                    "DELETE FROM schema_version WHERE version = ?",
                    (version,)
                )

    def _ensure_schema_version_table(self) -> None:
        """确保 schema_version 表存在"""
        with connect(self._db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version     INTEGER PRIMARY KEY,
                    name        TEXT NOT NULL,
                    applied_at  TEXT NOT NULL
                )
            """)

    def _extract_table_name(self, sql) -> str:
        """从 CREATE TABLE SQL 中提取表名"""
        import re
        match = re.search(r'CREATE\s+TABLE\s+(\w+)', sql, re.IGNORECASE)
        return match.group(1) if match else ""
