"""
WorkOps Database Task Repository
Sprint020: Persistence Foundation

使用 SQLite 持久化 Task
"""

import sqlite3

from .interfaces import WritableTaskRepository
from ..persistence.connection import connect
from ..persistence.errors import PersistenceValidationError, RepositoryConflictError


# Task 允许的字段
TASK_FIELDS = {"id", "operation_id", "operation_name", "device_id", "status", "start_time", "end_time", "duration"}

# 合法状态转换
ALLOWED_TRANSITIONS = {
    ("pending", "running"),
    ("pending", "cancelled"),
    ("running", "success"),
    ("running", "failed"),
}


class DatabaseTaskRepository(WritableTaskRepository):
    """Database Task Repository 实现"""

    def __init__(self, db_path):
        self._db_path = db_path

    def get_all(self) -> list:
        """获取所有任务"""
        with connect(self._db_path) as conn:
            rows = conn.execute("SELECT * FROM tasks").fetchall()
            return [dict(r) for r in rows]

    def get_by_id(self, task_id: str) -> dict:
        """根据 ID 获取任务"""
        with connect(self._db_path) as conn:
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
            return dict(row) if row else None

    def transition_status(self, task_id: str, expected_status: str, new_status: str) -> bool:
        """
        条件状态转换。
        
        使用单条条件 SQL：
        UPDATE tasks SET status = ? WHERE id = ? AND status = ?
        
        cursor.rowcount == 1 才返回 True
        """
        if (expected_status, new_status) not in ALLOWED_TRANSITIONS:
            return False

        with connect(self._db_path) as conn:
            cursor = conn.execute(
                "UPDATE tasks SET status = ? WHERE id = ? AND status = ?",
                (new_status, task_id, expected_status)
            )
            return cursor.rowcount == 1

    def add(self, task: dict) -> None:
        """
        插入新 Task
        
        规则：
        - 严格接受冻结的 8 个字段
        - id 必须非空
        - status 必须等于 pending
        - ID 已存在时 RepositoryConflictError
        """
        # 校验字段
        unknown_fields = set(task.keys()) - TASK_FIELDS
        if unknown_fields:
            raise PersistenceValidationError(f"Unknown fields: {unknown_fields}")

        # 校验 id
        if not task.get("id"):
            raise PersistenceValidationError("id is required")

        # 校验 status
        if task.get("status") != "pending":
            raise PersistenceValidationError("status must be pending")

        # 填充默认值
        task_with_defaults = {
            "id": task["id"],
            "operation_id": task.get("operation_id", ""),
            "operation_name": task.get("operation_name", ""),
            "device_id": task.get("device_id", ""),
            "status": "pending",
            "start_time": task.get("start_time", ""),
            "end_time": task.get("end_time", ""),
            "duration": task.get("duration", ""),
        }

        with connect(self._db_path) as conn:
            # 检查 ID 是否存在
            existing = conn.execute("SELECT 1 FROM tasks WHERE id = ?", (task["id"],)).fetchone()
            if existing:
                raise RepositoryConflictError(f"Task {task['id']} already exists")

            # 插入
            try:
                conn.execute(
                    """INSERT INTO tasks (id, operation_id, operation_name, device_id, status, start_time, end_time, duration)
                       VALUES (:id, :operation_id, :operation_name, :device_id, :status, :start_time, :end_time, :duration)""",
                    task_with_defaults
                )
            except sqlite3.IntegrityError as e:
                raise RepositoryConflictError(f"Failed to insert task: {e}")
