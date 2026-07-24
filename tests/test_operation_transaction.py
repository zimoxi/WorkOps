"""
WorkOps Operation Transaction Tests
Sprint056: Operation Transaction System Foundation

覆盖：
- TransactionStatus enum
- OperationTransaction validation
- RetryPolicy validation
- RecoveryAction enum
- RecoveryContract contract
- TransactionManager contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.transaction.status import TransactionStatus
from backup_manager.transaction.model import OperationTransaction
from backup_manager.transaction.retry import RetryPolicy
from backup_manager.transaction.recovery import RecoveryAction, RecoveryContract
from backup_manager.transaction.manager import TransactionManager
from backup_manager.transaction.errors import (
    TransactionError,
    InvalidTransactionError,
    TransactionConflictError,
    TransactionUnavailableError,
)


# ============================================================================
# TransactionStatus
# ============================================================================

class TestTransactionStatus(unittest.TestCase):
    """事务状态测试"""

    def test_created(self):
        self.assertEqual(TransactionStatus.CREATED.value, "created")

    def test_running(self):
        self.assertEqual(TransactionStatus.RUNNING.value, "running")

    def test_success(self):
        self.assertEqual(TransactionStatus.SUCCESS.value, "success")

    def test_failed(self):
        self.assertEqual(TransactionStatus.FAILED.value, "failed")

    def test_cancelled(self):
        self.assertEqual(TransactionStatus.CANCELLED.value, "cancelled")

    def test_five_statuses(self):
        self.assertEqual(len(TransactionStatus), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            TransactionStatus("nonexistent")


# ============================================================================
# OperationTransaction
# ============================================================================

class TestOperationTransaction(unittest.TestCase):
    """操作事务测试"""

    def _make_transaction(self, **kwargs):
        defaults = {
            "transaction_id": "txn-001",
            "operation_id": "op-001",
            "job_id": "j-001",
            "status": TransactionStatus.CREATED,
        }
        defaults.update(kwargs)
        return OperationTransaction(**defaults)

    def test_valid_transaction(self):
        txn = self._make_transaction()
        self.assertEqual(txn.transaction_id, "txn-001")
        self.assertEqual(txn.operation_id, "op-001")
        self.assertEqual(txn.job_id, "j-001")
        self.assertEqual(txn.status, TransactionStatus.CREATED)

    def test_frozen(self):
        txn = self._make_transaction()
        with self.assertRaises(AttributeError):
            txn.transaction_id = "other"

    def test_slots(self):
        txn = self._make_transaction()
        with self.assertRaises(AttributeError):
            txn.__dict__

    def test_empty_transaction_id_rejected(self):
        with self.assertRaises(InvalidTransactionError):
            self._make_transaction(transaction_id="")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidTransactionError):
            self._make_transaction(operation_id="")

    def test_empty_job_id_rejected(self):
        with self.assertRaises(InvalidTransactionError):
            self._make_transaction(job_id="")

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidTransactionError):
            self._make_transaction(status="created")

    def test_timezone_aware(self):
        txn = self._make_transaction()
        self.assertIsNotNone(txn.created_at.tzinfo)

    def test_all_statuses(self):
        for status in TransactionStatus:
            txn = self._make_transaction(status=status)
            self.assertEqual(txn.status, status)

    def test_no_forbidden_fields(self):
        txn = self._make_transaction()
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(txn, attr))

    def test_repr_no_secrets(self):
        txn = self._make_transaction()
        r = repr(txn)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# RetryPolicy
# ============================================================================

class TestRetryPolicy(unittest.TestCase):
    """重试策略测试"""

    def test_valid_policy(self):
        policy = RetryPolicy(max_attempts=3)
        self.assertEqual(policy.max_attempts, 3)
        self.assertTrue(policy.retry_enabled)

    def test_frozen(self):
        policy = RetryPolicy(max_attempts=3)
        with self.assertRaises(AttributeError):
            policy.max_attempts = 5

    def test_slots(self):
        policy = RetryPolicy(max_attempts=3)
        with self.assertRaises(AttributeError):
            policy.__dict__

    def test_negative_attempts_rejected(self):
        with self.assertRaises(InvalidTransactionError):
            RetryPolicy(max_attempts=-1)

    def test_zero_attempts_allowed(self):
        policy = RetryPolicy(max_attempts=0)
        self.assertEqual(policy.max_attempts, 0)

    def test_retry_disabled(self):
        policy = RetryPolicy(max_attempts=3, retry_enabled=False)
        self.assertFalse(policy.retry_enabled)

    def test_retry_enabled_must_be_bool(self):
        with self.assertRaises(InvalidTransactionError):
            RetryPolicy(max_attempts=3, retry_enabled=1)

    def test_no_forbidden_fields(self):
        policy = RetryPolicy(max_attempts=3)
        for attr in ["command", "secret", "credential"]:
            self.assertFalse(hasattr(policy, attr))


# ============================================================================
# RecoveryAction
# ============================================================================

class TestRecoveryAction(unittest.TestCase):
    """恢复动作测试"""

    def test_none(self):
        self.assertEqual(RecoveryAction.NONE.value, "none")

    def test_retry(self):
        self.assertEqual(RecoveryAction.RETRY.value, "retry")

    def test_abort(self):
        self.assertEqual(RecoveryAction.ABORT.value, "abort")

    def test_three_actions(self):
        self.assertEqual(len(RecoveryAction), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            RecoveryAction("nonexistent")


# ============================================================================
# RecoveryContract
# ============================================================================

class TestRecoveryContractContract(unittest.TestCase):
    """恢复契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RecoveryContract, ABC))

    def test_has_recover(self):
        self.assertTrue(hasattr(RecoveryContract, "recover"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RecoveryContract()

    def test_concrete_subclass(self):
        class MockRecovery(RecoveryContract):
            def recover(self, transaction):
                return RecoveryAction.RETRY
        recovery = MockRecovery()
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.FAILED,
        )
        action = recovery.recover(txn)
        self.assertEqual(action, RecoveryAction.RETRY)

    def test_missing_recover(self):
        class BadRecovery(RecoveryContract):
            pass
        with self.assertRaises(TypeError):
            BadRecovery()


# ============================================================================
# TransactionManager Contract
# ============================================================================

class TestTransactionManagerContract(unittest.TestCase):
    """事务管理器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(TransactionManager, ABC))

    def test_has_begin(self):
        self.assertTrue(hasattr(TransactionManager, "begin"))

    def test_has_complete(self):
        self.assertTrue(hasattr(TransactionManager, "complete"))

    def test_has_fail(self):
        self.assertTrue(hasattr(TransactionManager, "fail"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            TransactionManager()

    def test_concrete_subclass(self):
        class MockManager(TransactionManager):
            def begin(self, operation_id, job_id):
                return OperationTransaction(
                    transaction_id="txn-001", operation_id=operation_id,
                    job_id=job_id, status=TransactionStatus.CREATED,
                )
            def complete(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.SUCCESS,
                    created_at=transaction.created_at,
                )
            def fail(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.FAILED,
                    created_at=transaction.created_at,
                )
        manager = MockManager()
        txn = manager.begin("op-001", "j-001")
        self.assertEqual(txn.status, TransactionStatus.CREATED)
        completed = manager.complete(txn)
        self.assertEqual(completed.status, TransactionStatus.SUCCESS)
        failed = manager.fail(txn)
        self.assertEqual(failed.status, TransactionStatus.FAILED)

    def test_missing_begin(self):
        class BadManager(TransactionManager):
            def complete(self, transaction):
                pass
            def fail(self, transaction):
                pass
        with self.assertRaises(TypeError):
            BadManager()

    def test_missing_complete(self):
        class BadManager(TransactionManager):
            def begin(self, operation_id, job_id):
                pass
            def fail(self, transaction):
                pass
        with self.assertRaises(TypeError):
            BadManager()

    def test_missing_fail(self):
        class BadManager(TransactionManager):
            def begin(self, operation_id, job_id):
                pass
            def complete(self, transaction):
                pass
        with self.assertRaises(TypeError):
            BadManager()


# ============================================================================
# Error Model
# ============================================================================

class TestTransactionErrors(unittest.TestCase):
    """错误模型测试"""

    def test_transaction_error(self):
        with self.assertRaises(TransactionError):
            raise TransactionError("test")

    def test_invalid_transaction_error(self):
        with self.assertRaises(TransactionError):
            raise InvalidTransactionError("test")

    def test_conflict_error(self):
        exc = TransactionConflictError("txn-001")
        self.assertIn("txn-001", str(exc))

    def test_unavailable_error(self):
        with self.assertRaises(TransactionError):
            raise TransactionUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (TransactionError, ("test",)),
            (InvalidTransactionError, ("test",)),
            (TransactionConflictError, ("txn-001",)),
            (TransactionUnavailableError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_transaction_no_credentials(self):
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.CREATED,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(txn, attr))

    def test_retry_no_credentials(self):
        policy = RetryPolicy(max_attempts=3)
        for attr in ["command", "secret", "credential"]:
            self.assertFalse(hasattr(policy, attr))

    def test_no_subprocess(self):
        import ast
        import os
        txn_dir = os.path.join("backup_manager", "transaction")
        for filename in os.listdir(txn_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(txn_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and "subprocess" in node.module:
                        self.fail(f"subprocess imported in {filename}")

    def test_no_exec_eval(self):
        import ast
        import os
        txn_dir = os.path.join("backup_manager", "transaction")
        for filename in os.listdir(txn_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(txn_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_manager_lifecycle(self):
        """完整管理器生命周期"""
        class MockManager(TransactionManager):
            def begin(self, operation_id, job_id):
                return OperationTransaction(
                    transaction_id="txn-001", operation_id=operation_id,
                    job_id=job_id, status=TransactionStatus.CREATED,
                )
            def complete(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.SUCCESS,
                    created_at=transaction.created_at,
                )
            def fail(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.FAILED,
                    created_at=transaction.created_at,
                )
        manager = MockManager()
        txn = manager.begin("op-001", "j-001")
        self.assertEqual(txn.status, TransactionStatus.CREATED)
        completed = manager.complete(txn)
        self.assertEqual(completed.status, TransactionStatus.SUCCESS)


# ============================================================================
# Extended Tests
# ============================================================================

class TestTransactionExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidTransactionError, TransactionError))
        self.assertTrue(issubclass(TransactionConflictError, TransactionError))
        self.assertTrue(issubclass(TransactionUnavailableError, TransactionError))

    def test_transaction_repr_no_secrets(self):
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.CREATED,
        )
        r = repr(txn)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_retry_policy_repr_no_secrets(self):
        policy = RetryPolicy(max_attempts=3)
        r = repr(policy)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_transaction_preserves_all_fields(self):
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.CREATED,
        )
        self.assertEqual(txn.transaction_id, "txn-001")
        self.assertEqual(txn.operation_id, "op-001")
        self.assertEqual(txn.job_id, "j-001")
        self.assertEqual(txn.status, TransactionStatus.CREATED)

    def test_recovery_returns_action(self):
        class MockRecovery(RecoveryContract):
            def recover(self, transaction):
                return RecoveryAction.NONE
        recovery = MockRecovery()
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.FAILED,
        )
        action = recovery.recover(txn)
        self.assertIsInstance(action, RecoveryAction)

    def test_manager_returns_transaction(self):
        class MockManager(TransactionManager):
            def begin(self, operation_id, job_id):
                return OperationTransaction(
                    transaction_id="txn-001", operation_id=operation_id,
                    job_id=job_id, status=TransactionStatus.CREATED,
                )
            def complete(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.SUCCESS,
                    created_at=transaction.created_at,
                )
            def fail(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.FAILED,
                    created_at=transaction.created_at,
                )
        manager = MockManager()
        txn = manager.begin("op-001", "j-001")
        self.assertIsInstance(txn, OperationTransaction)

    def test_error_messages_safe(self):
        try:
            raise TransactionError("test")
        except TransactionError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_transaction_whitespace_id_rejected(self):
        with self.assertRaises(InvalidTransactionError):
            OperationTransaction(
                transaction_id="   ", operation_id="op-001",
                job_id="j-001", status=TransactionStatus.CREATED,
            )

    def test_retry_policy_large_attempts(self):
        policy = RetryPolicy(max_attempts=100)
        self.assertEqual(policy.max_attempts, 100)

    def test_transaction_no_command(self):
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.CREATED,
        )
        self.assertFalse(hasattr(txn, "command"))

    def test_transaction_no_ssh(self):
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.CREATED,
        )
        self.assertFalse(hasattr(txn, "ssh"))

    def test_manager_fail_returns_failed(self):
        class MockManager(TransactionManager):
            def begin(self, operation_id, job_id):
                return OperationTransaction(
                    transaction_id="txn-001", operation_id=operation_id,
                    job_id=job_id, status=TransactionStatus.CREATED,
                )
            def complete(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.SUCCESS,
                    created_at=transaction.created_at,
                )
            def fail(self, transaction):
                return OperationTransaction(
                    transaction_id=transaction.transaction_id,
                    operation_id=transaction.operation_id,
                    job_id=transaction.job_id,
                    status=TransactionStatus.FAILED,
                    created_at=transaction.created_at,
                )
        manager = MockManager()
        txn = manager.begin("op-001", "j-001")
        failed = manager.fail(txn)
        self.assertEqual(failed.status, TransactionStatus.FAILED)

    def test_recovery_abort_action(self):
        class MockRecovery(RecoveryContract):
            def recover(self, transaction):
                return RecoveryAction.ABORT
        recovery = MockRecovery()
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.FAILED,
        )
        action = recovery.recover(txn)
        self.assertEqual(action, RecoveryAction.ABORT)

    def test_retry_policy_no_secret(self):
        policy = RetryPolicy(max_attempts=3)
        self.assertFalse(hasattr(policy, "secret"))

    def test_transaction_no_token(self):
        txn = OperationTransaction(
            transaction_id="txn-001", operation_id="op-001",
            job_id="j-001", status=TransactionStatus.CREATED,
        )
        self.assertFalse(hasattr(txn, "token"))


if __name__ == "__main__":
    unittest.main()
