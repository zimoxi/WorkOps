"""
WorkOps RepositoryProvider — 集中式 Repository Provider
Sprint020: Persistence Foundation

缓存 Repository 实例
不自动运行 Migration
不自动建表
"""

from pathlib import Path

from .mock_task_repo import MockTaskRepository
from .mock_result_repo import MockExecutionResultRepository
from .db_task_repo import DatabaseTaskRepository
from .db_result_repo import DatabaseExecutionResultRepository
from ..persistence.config import PersistenceConfig
from ..persistence.migration import MigrationRunner
from ..persistence.errors import SchemaNotReadyError


class RepositoryProvider:
    """集中式 Repository Provider"""

    def __init__(self, config: PersistenceConfig):
        self._config = config
        self._task_repo = None
        self._result_repo = None

    def get_task_repository(self):
        """返回缓存的 Task Repository 实例"""
        if self._task_repo is None:
            if self._config.mode == "mock":
                self._task_repo = MockTaskRepository(self._config.context)
            elif self._config.mode == "database":
                self._check_schema_ready()
                self._task_repo = DatabaseTaskRepository(self._config.db_path)
        return self._task_repo

    def get_result_repository(self):
        """返回缓存的 ExecutionResult Repository 实例"""
        if self._result_repo is None:
            if self._config.mode == "mock":
                self._result_repo = MockExecutionResultRepository(self._config.context)
            elif self._config.mode == "database":
                self._check_schema_ready()
                self._result_repo = DatabaseExecutionResultRepository(self._config.db_path)
        return self._result_repo

    def _check_schema_ready(self):
        """检查 Schema 是否已升级到当前最新版本"""
        db_path = self._config.db_path
        if not Path(db_path).exists():
            raise SchemaNotReadyError("Database file does not exist")

        runner = MigrationRunner(db_path)
        runner.validate_schema()

        current = runner.current_version()
        latest = runner.latest_version()
        if current < latest:
            raise SchemaNotReadyError(
                f"Schema not upgraded to latest version: current={current}, latest={latest}"
            )
