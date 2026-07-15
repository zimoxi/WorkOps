"""
WorkOps Database ExecutionResult Repository
Sprint020: Persistence Foundation

使用 SQLite 持久化 ExecutionResult
"""

import sqlite3

from .interfaces import ExecutionResultRepository
from ..persistence.connection import connect
from ..persistence.errors import PersistenceValidationError, RepositoryConflictError


# ExecutionResult 允许的字段
RESULT_FIELDS = {"task_id", "status", "started_at", "finished_at", "duration", "stdout", "stderr", "exit_code", "message"}


class DatabaseExecutionResultRepository(ExecutionResultRepository):
    """Database ExecutionResult Repository 实现"""

    def __init__(self, db_path):
        self._db_path = db_path

    def save(self, result: dict) -> None:
        """
        保存 ExecutionResult
        
        规则：
        - 首次保存允许
        - 相同 task_id、相同内容：幂等 no-op
        - 相同 task_id、不同内容：RepositoryConflictError
        """
        # 校验字段
        unknown_fields = set(result.keys()) - RESULT_FIELDS
        if unknown_fields:
            raise PersistenceValidationError(f"Unknown fields: {unknown_fields}")

        with connect(self._db_path) as conn:
            existing = conn.execute(
                "SELECT * FROM execution_results WHERE task_id = ?",
                (result["task_id"],)
            ).fetchone()

            if existing:
                existing_dict = dict(existing)
                if existing_dict == result:
                    return  # 幂等 no-op
                raise RepositoryConflictError(
                    f"Result for task {result['task_id']} already exists with different content"
                )

            try:
                conn.execute(
                    """INSERT INTO execution_results (task_id, status, started_at, finished_at, duration, stdout, stderr, exit_code, message)
                       VALUES (:task_id, :status, :started_at, :finished_at, :duration, :stdout, :stderr, :exit_code, :message)""",
                    result
                )
            except sqlite3.IntegrityError as e:
                raise RepositoryConflictError(f"Failed to save result: {e}")

    def get_by_task_id(self, task_id: str) -> dict:
        """根据 task_id 获取"""
        with connect(self._db_path) as conn:
            row = conn.execute(
                "SELECT * FROM execution_results WHERE task_id = ?",
                (task_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all(self) -> list:
        """获取所有"""
        with connect(self._db_path) as conn:
            rows = conn.execute("SELECT * FROM execution_results").fetchall()
            return [dict(r) for r in rows]
