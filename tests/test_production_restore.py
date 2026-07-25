"""
WorkOps Production Restore Execution Tests
Sprint062: Production Restore Execution Foundation

覆盖：
- ProductionRestoreStatus enum
- ProductionRestoreRequest validation
- ProductionRestoreResult validation
- RestoreRuntimeDispatcher contract
- ProductionRestoreExecutor contract
- validate_production_restore_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.production_restore.model import (
    ProductionRestoreStatus,
    ProductionRestoreRequest,
    validate_production_restore_request,
)
from backup_manager.production_restore.result import ProductionRestoreResult
from backup_manager.production_restore.dispatcher import RestoreRuntimeDispatcher
from backup_manager.production_restore.executor import ProductionRestoreExecutor
from backup_manager.production_restore.errors import (
    ProductionRestoreError,
    InvalidProductionRestoreRequestError,
    RestoreRuntimeDispatchError,
    ProductionRestoreUnavailableError,
)


# ============================================================================
# ProductionRestoreStatus
# ============================================================================

class TestProductionRestoreStatus(unittest.TestCase):
    """生产恢复状态测试"""

    def test_created(self):
        self.assertEqual(ProductionRestoreStatus.CREATED.value, "created")

    def test_validating(self):
        self.assertEqual(ProductionRestoreStatus.VALIDATING.value, "validating")

    def test_executing(self):
        self.assertEqual(ProductionRestoreStatus.EXECUTING.value, "executing")

    def test_completed(self):
        self.assertEqual(ProductionRestoreStatus.COMPLETED.value, "completed")

    def test_failed(self):
        self.assertEqual(ProductionRestoreStatus.FAILED.value, "failed")

    def test_five_statuses(self):
        self.assertEqual(len(ProductionRestoreStatus), 5)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            ProductionRestoreStatus("nonexistent")


# ============================================================================
# ProductionRestoreRequest
# ============================================================================

class TestProductionRestoreRequest(unittest.TestCase):
    """生产恢复请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "restore_id": "r-001",
            "backup_id": "b-001",
            "execution_id": "exec-001",
            "transaction_id": "txn-001",
            "adapter_id": "linux-001",
            "runtime_type": "ssh",
        }
        defaults.update(kwargs)
        return ProductionRestoreRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.restore_id, "r-001")
        self.assertEqual(req.backup_id, "b-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.transaction_id, "txn-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.runtime_type, "ssh")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.restore_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            self._make_request(restore_id="")

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            self._make_request(backup_id="")

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            self._make_request(execution_id="")

    def test_empty_transaction_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            self._make_request(transaction_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            self._make_request(adapter_id="")

    def test_empty_runtime_type_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            self._make_request(runtime_type="")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "token", "command", "ssh", "api_key"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# ProductionRestoreResult
# ============================================================================

class TestProductionRestoreResult(unittest.TestCase):
    """生产恢复结果测试"""

    def test_valid_result(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertEqual(result.restore_id, "r-001")
        self.assertTrue(result.success)
        self.assertEqual(result.status, ProductionRestoreStatus.COMPLETED)

    def test_frozen(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.restore_id = "other"

    def test_slots(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_restore_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            ProductionRestoreResult(
                restore_id="", status=ProductionRestoreStatus.COMPLETED,
                success=True, message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            ProductionRestoreResult(
                restore_id="r-001", status="completed",
                success=True, message="ok",
            )

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            ProductionRestoreResult(
                restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
                success=1, message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            ProductionRestoreResult(
                restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
                success=True, message=123,
            )

    def test_timezone_aware(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_all_statuses(self):
        for status in ProductionRestoreStatus:
            result = ProductionRestoreResult(
                restore_id="r-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_no_forbidden_fields(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_failed_result(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.FAILED,
            success=False, message="error",
        )
        self.assertFalse(result.success)


# ============================================================================
# RestoreRuntimeDispatcher Contract
# ============================================================================

class TestRestoreRuntimeDispatcherContract(unittest.TestCase):
    """恢复运行时分发器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreRuntimeDispatcher, ABC))

    def test_has_dispatch(self):
        self.assertTrue(hasattr(RestoreRuntimeDispatcher, "dispatch"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreRuntimeDispatcher()

    def test_concrete_subclass(self):
        class MockDispatcher(RestoreRuntimeDispatcher):
            def dispatch(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="ok",
                )
        dispatcher = MockDispatcher()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_missing_dispatch(self):
        class BadDispatcher(RestoreRuntimeDispatcher):
            pass
        with self.assertRaises(TypeError):
            BadDispatcher()


# ============================================================================
# ProductionRestoreExecutor Contract
# ============================================================================

class TestProductionRestoreExecutorContract(unittest.TestCase):
    """生产恢复执行器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(ProductionRestoreExecutor, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(ProductionRestoreExecutor, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            ProductionRestoreExecutor()

    def test_concrete_subclass(self):
        class MockExecutor(ProductionRestoreExecutor):
            def execute(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_missing_execute(self):
        class BadExecutor(ProductionRestoreExecutor):
            pass
        with self.assertRaises(TypeError):
            BadExecutor()


# ============================================================================
# validate_production_restore_request
# ============================================================================

class TestValidateProductionRestoreRequest(unittest.TestCase):
    """验证生产恢复请求测试"""

    def test_valid_request(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        validate_production_restore_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            validate_production_restore_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestProductionRestoreErrors(unittest.TestCase):
    """错误模型测试"""

    def test_restore_error(self):
        with self.assertRaises(ProductionRestoreError):
            raise ProductionRestoreError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(ProductionRestoreError):
            raise InvalidProductionRestoreRequestError("test")

    def test_dispatch_error(self):
        with self.assertRaises(ProductionRestoreError):
            raise RestoreRuntimeDispatchError("test")

    def test_unavailable_error(self):
        with self.assertRaises(ProductionRestoreError):
            raise ProductionRestoreUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (ProductionRestoreError, ("test",)),
            (InvalidProductionRestoreRequestError, ("test",)),
            (RestoreRuntimeDispatchError, ("test",)),
            (ProductionRestoreUnavailableError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_request_no_credentials(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        for attr in ["password", "credential", "secret", "token", "command", "ssh", "api_key"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        for attr in ["stdout", "stderr", "command", "secret", "credential", "token"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        pr_dir = os.path.join("backup_manager", "production_restore")
        for filename in os.listdir(pr_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(pr_dir, filename)
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
        pr_dir = os.path.join("backup_manager", "production_restore")
        for filename in os.listdir(pr_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(pr_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_executor_lifecycle(self):
        """完整执行器生命周期"""
        class MockExecutor(ProductionRestoreExecutor):
            def execute(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = executor.execute(req)
        self.assertTrue(result.success)
        self.assertEqual(result.status, ProductionRestoreStatus.COMPLETED)

    def test_dispatcher_lifecycle(self):
        """完整分发器生命周期"""
        class MockDispatcher(RestoreRuntimeDispatcher):
            def dispatch(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="ok",
                )
        dispatcher = MockDispatcher()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)


# ============================================================================
# Extended Tests
# ============================================================================

class TestProductionRestoreExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidProductionRestoreRequestError, ProductionRestoreError))
        self.assertTrue(issubclass(RestoreRuntimeDispatchError, ProductionRestoreError))
        self.assertTrue(issubclass(ProductionRestoreUnavailableError, ProductionRestoreError))

    def test_request_repr_no_secrets(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_preserves_all_fields(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertEqual(req.restore_id, "r-001")
        self.assertEqual(req.backup_id, "b-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.transaction_id, "txn-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.runtime_type, "ssh")

    def test_executor_returns_result(self):
        class MockExecutor(ProductionRestoreExecutor):
            def execute(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="ok",
                )
        executor = MockExecutor()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = executor.execute(req)
        self.assertIsInstance(result, ProductionRestoreResult)

    def test_dispatcher_returns_result(self):
        class MockDispatcher(RestoreRuntimeDispatcher):
            def dispatch(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="ok",
                )
        dispatcher = MockDispatcher()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = dispatcher.dispatch(req)
        self.assertIsInstance(result, ProductionRestoreResult)

    def test_request_all_runtime_types(self):
        for rt in ["ssh", "pve_api", "omv_api"]:
            req = ProductionRestoreRequest(
                restore_id="r-001", backup_id="b-001", execution_id="exec-001",
                transaction_id="txn-001", adapter_id="linux-001", runtime_type=rt,
            )
            self.assertEqual(req.runtime_type, rt)

    def test_result_all_statuses(self):
        for status in ProductionRestoreStatus:
            result = ProductionRestoreResult(
                restore_id="r-001", status=status,
                success=True, message="ok",
            )
            self.assertEqual(result.status, status)

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            ProductionRestoreRequest(
                restore_id="   ", backup_id="b-001", execution_id="exec-001",
                transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
            )

    def test_result_empty_message_accepted(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="",
        )
        self.assertEqual(result.message, "")

    def test_request_no_command(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "command"))

    def test_request_no_api_key(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "api_key"))

    def test_result_no_stderr(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stderr"))

    def test_error_messages_safe(self):
        try:
            raise ProductionRestoreError("test")
        except ProductionRestoreError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_dispatch_error_message(self):
        exc = RestoreRuntimeDispatchError("dispatch failed")
        self.assertIn("dispatch failed", str(exc))

    def test_unavailable_error_message(self):
        exc = ProductionRestoreUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_executor_failed_result(self):
        class MockExecutor(ProductionRestoreExecutor):
            def execute(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.FAILED,
                    success=False, message="error",
                )
        executor = MockExecutor()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = executor.execute(req)
        self.assertFalse(result.success)

    def test_dispatcher_pve_runtime(self):
        class MockDispatcher(RestoreRuntimeDispatcher):
            def dispatch(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="pve ok",
                )
        dispatcher = MockDispatcher()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="pve-001", runtime_type="pve_api",
        )
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_dispatcher_omv_runtime(self):
        class MockDispatcher(RestoreRuntimeDispatcher):
            def dispatch(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.COMPLETED,
                    success=True, message="omv ok",
                )
        dispatcher = MockDispatcher()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="omv-001", runtime_type="omv_api",
        )
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_request_no_password(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "password"))

    def test_request_no_secret(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "secret"))

    def test_request_no_credential(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "credential"))

    def test_request_no_token(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "token"))

    def test_request_no_ssh(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "ssh"))

    def test_result_no_secret(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "secret"))

    def test_result_no_token(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "token"))

    def test_result_no_credential(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "credential"))

    def test_result_no_command(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "command"))

    def test_result_no_stdout(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertFalse(hasattr(result, "stdout"))

    def test_request_no_credential_value(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "credential_value"))

    def test_request_no_private_key(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertFalse(hasattr(req, "private_key"))

    def test_request_all_fields_present(self):
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        self.assertTrue(hasattr(req, "restore_id"))
        self.assertTrue(hasattr(req, "backup_id"))
        self.assertTrue(hasattr(req, "execution_id"))
        self.assertTrue(hasattr(req, "transaction_id"))
        self.assertTrue(hasattr(req, "adapter_id"))
        self.assertTrue(hasattr(req, "runtime_type"))
        self.assertTrue(hasattr(req, "created_at"))

    def test_result_all_fields_present(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.COMPLETED,
            success=True, message="ok",
        )
        self.assertTrue(hasattr(result, "restore_id"))
        self.assertTrue(hasattr(result, "status"))
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "message"))
        self.assertTrue(hasattr(result, "completed_at"))

    def test_request_validating_status(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.VALIDATING,
            success=True, message="validating",
        )
        self.assertEqual(result.status, ProductionRestoreStatus.VALIDATING)

    def test_request_executing_status(self):
        result = ProductionRestoreResult(
            restore_id="r-001", status=ProductionRestoreStatus.EXECUTING,
            success=True, message="executing",
        )
        self.assertEqual(result.status, ProductionRestoreStatus.EXECUTING)

    def test_request_whitespace_runtime_type_rejected(self):
        with self.assertRaises(InvalidProductionRestoreRequestError):
            ProductionRestoreRequest(
                restore_id="r-001", backup_id="b-001", execution_id="exec-001",
                transaction_id="txn-001", adapter_id="linux-001", runtime_type="   ",
            )

    def test_dispatcher_failed_result(self):
        class MockDispatcher(RestoreRuntimeDispatcher):
            def dispatch(self, request):
                return ProductionRestoreResult(
                    restore_id=request.restore_id,
                    status=ProductionRestoreStatus.FAILED,
                    success=False, message="error",
                )
        dispatcher = MockDispatcher()
        req = ProductionRestoreRequest(
            restore_id="r-001", backup_id="b-001", execution_id="exec-001",
            transaction_id="txn-001", adapter_id="linux-001", runtime_type="ssh",
        )
        result = dispatcher.dispatch(req)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
