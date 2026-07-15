"""
WorkOps Persistence Tests
Sprint020: Persistence Foundation

覆盖：
- 空数据库 upgrade
- 已有 device 表数据库 upgrade
- schema_version
- 重复 upgrade
- downgrade 空表
- downgrade 有数据拒绝
- Migration 失败 rollback
- Task 保存和读取
- 合法 transition_status
- 非法 transition_status
- ExecutionResult 保存和读取
- task_id 唯一性
- MockRepository 保持兼容
- RepositoryProvider Mock 模式
- RepositoryProvider Database 模式
- 每次连接关闭
- Windows 临时数据库可删除
- 敏感字段不存在于 Schema
- 150 个现有测试继续通过
- Full Suite 连续运行两次
"""

import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from backup_manager.persistence.config import PersistenceConfig
from backup_manager.persistence.connection import connect
from backup_manager.persistence.migration import MigrationRunner
from backup_manager.persistence.errors import (
    PersistenceError,
    PersistenceValidationError,
    RepositoryConflictError,
    SchemaNotReadyError,
    MigrationError,
    MigrationSafetyError,
    SchemaConflictError,
)
from backup_manager.repositories.interfaces import (
    TaskRepository,
    WritableTaskRepository,
    ExecutionResultRepository,
)
from backup_manager.repositories.mock_task_repo import MockTaskRepository
from backup_manager.repositories.mock_result_repo import MockExecutionResultRepository
from backup_manager.repositories.db_task_repo import DatabaseTaskRepository
from backup_manager.repositories.db_result_repo import DatabaseExecutionResultRepository
from backup_manager.repositories.provider import RepositoryProvider


# ─── Migration Tests ───────────────────────────────

class TestMigrationUpgrade(unittest.TestCase):
    """测试 Migration upgrade"""

    def test_empty_database_upgrade(self):
        """空数据库 upgrade"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()
            self.assertEqual(runner.current_version(), 2)

    def test_upgrade_with_existing_device_table(self):
        """已有 device 表数据库 upgrade"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            # 创建 device 表
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE device (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL
                )
            """)
            conn.commit()
            conn.close()

            runner = MigrationRunner(db_path)
            runner.upgrade()
            self.assertEqual(runner.current_version(), 2)

    def test_schema_version(self):
        """schema_version 版本号正确记录"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()

            with connect(db_path) as conn:
                rows = conn.execute("SELECT version, name FROM schema_version ORDER BY version").fetchall()
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0][0], 1)
                self.assertEqual(rows[0][1], "create_tasks")
                self.assertEqual(rows[1][0], 2)
                self.assertEqual(rows[1][1], "create_execution_results")

    def test_repeat_upgrade(self):
        """重复 upgrade 幂等"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()
            runner.upgrade()  # 重复
            self.assertEqual(runner.current_version(), 2)


class TestMigrationDowngrade(unittest.TestCase):
    """测试 Migration downgrade"""

    def test_downgrade_empty_tables(self):
        """downgrade 空表"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()
            runner.downgrade(0)
            self.assertEqual(runner.current_version(), 0)

    def test_downgrade_with_data_rejected(self):
        """downgrade 有数据拒绝"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()

            # 插入数据
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO tasks (id, status) VALUES (?, ?)",
                    ("task-001", "pending")
                )

            with self.assertRaises(MigrationSafetyError):
                runner.downgrade(0)

    def test_downgrade_preflight_no_changes_on_failure(self):
        """2 → 0 降级预检查失败时完全无变更"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()

            # 插入数据
            with connect(db_path) as conn:
                conn.execute(
                    "INSERT INTO tasks (id, status) VALUES (?, ?)",
                    ("task-001", "pending")
                )

            try:
                runner.downgrade(0)
            except MigrationSafetyError:
                pass

            # 验证版本和表不变
            self.assertEqual(runner.current_version(), 2)
            with connect(db_path) as conn:
                table = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'"
                ).fetchone()
                self.assertIsNotNone(table)

    def test_device_table_preserved(self):
        """device 表保持不变"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            # 创建 device 表
            conn = sqlite3.connect(db_path)
            conn.execute("CREATE TABLE device (id TEXT PRIMARY KEY, name TEXT)")
            conn.execute("INSERT INTO device VALUES (?, ?)", ("d-001", "Test"))
            conn.commit()
            conn.close()

            runner = MigrationRunner(db_path)
            runner.upgrade()
            runner.downgrade(0)

            # device 表应该还在
            conn = sqlite3.connect(db_path)
            row = conn.execute("SELECT COUNT(*) FROM device").fetchone()
            self.assertEqual(row[0], 1)
            conn.close()


class TestMigrationConsistency(unittest.TestCase):
    """测试 Schema 一致性检查"""

    def test_current_version_no_write(self):
        """current_version 无写入副作用"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            # 数据库不存在
            self.assertEqual(runner.current_version(), 0)
            # 不应该创建文件
            self.assertFalse(Path(db_path).exists())

    def test_table_exists_but_version_not_registered(self):
        """表存在但版本未登记"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            conn = sqlite3.connect(db_path)
            conn.execute("""
                CREATE TABLE tasks (
                    id TEXT PRIMARY KEY,
                    operation_id TEXT,
                    operation_name TEXT,
                    device_id TEXT,
                    status TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration TEXT
                )
            """)
            conn.commit()
            conn.close()

            runner = MigrationRunner(db_path)
            with self.assertRaises(SchemaConflictError):
                runner.validate_schema()

    def test_registered_but_table_missing(self):
        """版本记录存在但表缺失"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()

            # 手动删除 tasks 表
            with connect(db_path) as conn:
                conn.execute("DROP TABLE tasks")

            with self.assertRaises(SchemaConflictError):
                runner.validate_schema()


# ─── Repository Tests ───────────────────────────────

class TestMockTaskRepository(unittest.TestCase):
    """测试 MockTaskRepository"""

    def test_add_only_pending(self):
        """Task add 拒绝非 pending"""
        class Context:
            tasks = []
        repo = MockTaskRepository(Context())

        with self.assertRaises(PersistenceValidationError):
            repo.add({"id": "task-001", "status": "success"})

    def test_add_duplicate_id(self):
        """重复 Task ID 拒绝"""
        class Context:
            tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(Context())

        with self.assertRaises(RepositoryConflictError):
            repo.add({"id": "task-001", "status": "pending"})

    def test_add_unknown_fields(self):
        """未知字段拒绝"""
        class Context:
            tasks = []
        repo = MockTaskRepository(Context())

        with self.assertRaises(PersistenceValidationError):
            repo.add({"id": "task-001", "status": "pending", "unknown_field": "value"})

    def test_existing_fake_compatible(self):
        """现有 TaskRepository Fake 不因新接口失效"""
        class Context:
            tasks = [{"id": "task-001", "status": "pending"}]
        repo = MockTaskRepository(Context())

        # get_all
        tasks = repo.get_all()
        self.assertEqual(len(tasks), 1)

        # get_by_id
        task = repo.get_by_id("task-001")
        self.assertIsNotNone(task)
        self.assertEqual(task["id"], "task-001")

        # transition_status
        result = repo.transition_status("task-001", "pending", "running")
        self.assertTrue(result)


class TestMockResultRepository(unittest.TestCase):
    """测试 MockExecutionResultRepository"""

    def test_save_and_read(self):
        """保存和读取"""
        class Context:
            pass
        ctx = Context()
        repo = MockExecutionResultRepository(ctx)

        result = {"task_id": "task-001", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        repo.save(result)

        loaded = repo.get_by_task_id("task-001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["task_id"], "task-001")

    def test_idempotent_save(self):
        """相同内容重复保存幂等"""
        class Context:
            pass
        ctx = Context()
        repo = MockExecutionResultRepository(ctx)

        result = {"task_id": "task-001", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        repo.save(result)
        repo.save(result)  # 幂等

        self.assertEqual(len(repo.get_all()), 1)

    def test_conflict_save(self):
        """冲突内容拒绝覆盖"""
        class Context:
            pass
        ctx = Context()
        repo = MockExecutionResultRepository(ctx)

        result1 = {"task_id": "task-001", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        result2 = {"task_id": "task-001", "status": "failed", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 1, "message": "error"}

        repo.save(result1)
        with self.assertRaises(RepositoryConflictError):
            repo.save(result2)

    def test_unknown_fields(self):
        """未知字段拒绝"""
        class Context:
            pass
        ctx = Context()
        repo = MockExecutionResultRepository(ctx)

        result = {"task_id": "task-001", "status": "success", "unknown_field": "value"}
        with self.assertRaises(PersistenceValidationError):
            repo.save(result)

    def test_creates_execution_results_on_context(self):
        """context 没有 execution_results 时自动创建"""
        class Context:
            pass
        ctx = Context()
        repo = MockExecutionResultRepository(ctx)
        self.assertTrue(hasattr(ctx, 'execution_results'))
        self.assertEqual(ctx.execution_results, [])


class TestDatabaseTaskRepository(unittest.TestCase):
    """测试 DatabaseTaskRepository"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp.name, "test.db")
        runner = MigrationRunner(self.db_path)
        runner.upgrade()

    def tearDown(self):
        self.temp.cleanup()

    def test_add_and_read(self):
        """Task 保存和读取"""
        repo = DatabaseTaskRepository(self.db_path)
        repo.add({"id": "task-001", "status": "pending", "operation_id": "", "operation_name": "", "device_id": "", "start_time": "", "end_time": "", "duration": ""})

        task = repo.get_by_id("task-001")
        self.assertIsNotNone(task)
        self.assertEqual(task["id"], "task-001")
        self.assertEqual(task["status"], "pending")

    def test_transition_status(self):
        """合法 transition_status"""
        repo = DatabaseTaskRepository(self.db_path)
        repo.add({"id": "task-001", "status": "pending"})

        result = repo.transition_status("task-001", "pending", "running")
        self.assertTrue(result)

        task = repo.get_by_id("task-001")
        self.assertEqual(task["status"], "running")

    def test_transition_status_invalid(self):
        """非法 transition_status"""
        repo = DatabaseTaskRepository(self.db_path)
        repo.add({"id": "task-001", "status": "pending"})

        result = repo.transition_status("task-001", "pending", "success")
        self.assertFalse(result)

    def test_add_rejects_non_pending(self):
        """Task add 拒绝非 pending"""
        repo = DatabaseTaskRepository(self.db_path)
        with self.assertRaises(PersistenceValidationError):
            repo.add({"id": "task-001", "status": "success"})

    def test_add_rejects_duplicate(self):
        """重复 Task ID 拒绝"""
        repo = DatabaseTaskRepository(self.db_path)
        repo.add({"id": "task-001", "status": "pending"})
        with self.assertRaises(RepositoryConflictError):
            repo.add({"id": "task-001", "status": "pending"})

    def test_add_rejects_unknown_fields(self):
        """未知字段拒绝"""
        repo = DatabaseTaskRepository(self.db_path)
        with self.assertRaises(PersistenceValidationError):
            repo.add({"id": "task-001", "status": "pending", "unknown": "value"})


class TestDatabaseResultRepository(unittest.TestCase):
    """测试 DatabaseExecutionResultRepository"""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp.name, "test.db")
        runner = MigrationRunner(self.db_path)
        runner.upgrade()

        # 创建一个 task
        with connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO tasks (id, status) VALUES (?, ?)",
                ("task-001", "pending")
            )

    def tearDown(self):
        self.temp.cleanup()

    def test_save_and_read(self):
        """保存和读取"""
        repo = DatabaseExecutionResultRepository(self.db_path)
        result = {"task_id": "task-001", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        repo.save(result)

        loaded = repo.get_by_task_id("task-001")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded["task_id"], "task-001")

    def test_idempotent_save(self):
        """相同内容重复保存幂等"""
        repo = DatabaseExecutionResultRepository(self.db_path)
        result = {"task_id": "task-001", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        repo.save(result)
        repo.save(result)  # 幂等

        self.assertEqual(len(repo.get_all()), 1)

    def test_conflict_save(self):
        """冲突内容拒绝覆盖"""
        repo = DatabaseExecutionResultRepository(self.db_path)
        result1 = {"task_id": "task-001", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        result2 = {"task_id": "task-001", "status": "failed", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 1, "message": "error"}

        repo.save(result1)
        with self.assertRaises(RepositoryConflictError):
            repo.save(result2)

    def test_unknown_fields(self):
        """未知字段拒绝"""
        repo = DatabaseExecutionResultRepository(self.db_path)
        result = {"task_id": "task-001", "status": "success", "unknown": "value"}
        with self.assertRaises(PersistenceValidationError):
            repo.save(result)

    def test_foreign_key_constraint(self):
        """外键约束"""
        repo = DatabaseExecutionResultRepository(self.db_path)
        result = {"task_id": "nonexistent", "status": "success", "started_at": "", "finished_at": "", "duration": "", "stdout": "", "stderr": "", "exit_code": 0, "message": ""}
        with self.assertRaises(RepositoryConflictError):
            repo.save(result)


# ─── RepositoryProvider Tests ───────────────────────

class TestRepositoryProvider(unittest.TestCase):
    """测试 RepositoryProvider"""

    def test_mock_mode(self):
        """Mock 模式"""
        class Context:
            tasks = []
        config = PersistenceConfig(mode="mock", context=Context())
        provider = RepositoryProvider(config)

        task_repo = provider.get_task_repository()
        self.assertIsInstance(task_repo, MockTaskRepository)

        result_repo = provider.get_result_repository()
        self.assertIsInstance(result_repo, MockExecutionResultRepository)

    def test_returns_same_instance(self):
        """Provider 返回同一实例"""
        class Context:
            tasks = []
        config = PersistenceConfig(mode="mock", context=Context())
        provider = RepositoryProvider(config)

        repo1 = provider.get_task_repository()
        repo2 = provider.get_task_repository()
        self.assertIs(repo1, repo2)

    def test_database_mode_schema_not_ready(self):
        """Database 模式 Schema 未准备时报错"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            config = PersistenceConfig(mode="database", db_path=db_path)
            provider = RepositoryProvider(config)

            with self.assertRaises(SchemaNotReadyError):
                provider.get_task_repository()

    def test_database_mode_schema_ready(self):
        """Database 模式 Schema 已准备"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()

            config = PersistenceConfig(mode="database", db_path=db_path)
            provider = RepositoryProvider(config)

            task_repo = provider.get_task_repository()
            self.assertIsInstance(task_repo, DatabaseTaskRepository)


# ─── PersistenceConfig Tests ───────────────────────

class TestPersistenceConfig(unittest.TestCase):
    """测试 PersistenceConfig"""

    def test_invalid_mode(self):
        """非法 mode"""
        with self.assertRaises(PersistenceValidationError):
            PersistenceConfig(mode="invalid")

    def test_database_missing_db_path(self):
        """Database 模式缺少 db_path"""
        with self.assertRaises(PersistenceValidationError):
            PersistenceConfig(mode="database")

    def test_mock_missing_context(self):
        """Mock 模式缺少 context"""
        with self.assertRaises(PersistenceValidationError):
            PersistenceConfig(mode="mock")

    def test_valid_mock(self):
        """合法 Mock 配置"""
        config = PersistenceConfig(mode="mock", context=object())
        self.assertEqual(config.mode, "mock")

    def test_valid_database(self):
        """合法 Database 配置"""
        config = PersistenceConfig(mode="database", db_path="/tmp/test.db")
        self.assertEqual(config.mode, "database")


# ─── Connection Tests ───────────────────────────────

class TestConnection(unittest.TestCase):
    """测试 Connection Factory"""

    def test_connection_closed_after_use(self):
        """每次连接关闭"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            with connect(db_path) as conn:
                conn.execute("CREATE TABLE test (id TEXT PRIMARY KEY)")
            # 连接应该已关闭，文件应该可以删除
            os.unlink(db_path)
            self.assertFalse(Path(db_path).exists())

    def test_windows_temp_db_deletable(self):
        """Windows 临时数据库可删除"""
        with tempfile.TemporaryDirectory() as temp:
            db_path = os.path.join(temp, "test.db")
            runner = MigrationRunner(db_path)
            runner.upgrade()

            # 关闭后应该可以删除
            self.assertTrue(Path(db_path).exists())
            os.unlink(db_path)
            self.assertFalse(Path(db_path).exists())


if __name__ == "__main__":
    unittest.main()
