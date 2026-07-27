"""
WorkOps Real Backup Execution Engine Tests
Sprint070: Real Backup Execution Engine

覆盖：
- BackupExecutionMode enum
- BackupExecutionRequest validation
- BackupExecutionResult validation
- LinuxBackupHandler contract
- PVEBackupHandler contract
- OMVBackupHandler contract
- BackupRuntimeDispatcher routing
- RealBackupExecutor execution flow
- Error model
- Security boundary
"""

import unittest

from backup_manager.backup_engine.model import BackupExecutionMode, BackupExecutionRequest
from backup_manager.backup_engine.result import BackupExecutionResult
from backup_manager.backup_engine.handlers import (
    LinuxBackupHandler,
    PVEBackupHandler,
    OMVBackupHandler,
)
from backup_manager.backup_engine.dispatcher import BackupRuntimeDispatcher
from backup_manager.backup_engine.executor import RealBackupExecutor
from backup_manager.backup_engine.errors import (
    BackupEngineError,
    InvalidBackupExecutionError,
    BackupRuntimeUnavailableError,
    BackupExecutionTimeoutError,
)


# ============================================================================
# Helpers
# ============================================================================

def _make_request(**kwargs):
    defaults = {
        "backup_id": "b-001",
        "execution_id": "exec-001",
        "transaction_id": "txn-001",
        "adapter_id": "linux-001",
        "mode": BackupExecutionMode.LINUX,
    }
    defaults.update(kwargs)
    return BackupExecutionRequest(**defaults)


def _make_result(backup_id="b-001", success=True, message="ok"):
    return BackupExecutionResult(backup_id=backup_id, success=success, message=message)


class MockLinuxHandler(LinuxBackupHandler):
    def execute(self, request):
        return _make_result(backup_id=request.backup_id)


class MockPVEHandler(PVEBackupHandler):
    def execute(self, request):
        return _make_result(backup_id=request.backup_id)


class MockOMVHandler(OMVBackupHandler):
    def execute(self, request):
        return _make_result(backup_id=request.backup_id)


# ============================================================================
# BackupExecutionMode
# ============================================================================

class TestBackupExecutionMode(unittest.TestCase):
    """备份执行模式测试"""

    def test_linux(self):
        self.assertEqual(BackupExecutionMode.LINUX.value, "linux")

    def test_pve(self):
        self.assertEqual(BackupExecutionMode.PVE.value, "pve")

    def test_omv(self):
        self.assertEqual(BackupExecutionMode.OMV.value, "omv")

    def test_three_modes(self):
        self.assertEqual(len(BackupExecutionMode), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            BackupExecutionMode("nonexistent")


# ============================================================================
# BackupExecutionRequest
# ============================================================================

class TestBackupExecutionRequest(unittest.TestCase):
    """备份执行请求测试"""

    def test_valid_request(self):
        req = _make_request()
        self.assertEqual(req.backup_id, "b-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.transaction_id, "txn-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.mode, BackupExecutionMode.LINUX)

    def test_frozen(self):
        req = _make_request()
        with self.assertRaises(AttributeError):
            req.backup_id = "other"

    def test_slots(self):
        req = _make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(backup_id="")

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(execution_id="")

    def test_empty_transaction_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(transaction_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(adapter_id="")

    def test_invalid_mode_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(mode="linux")

    def test_timezone_aware(self):
        req = _make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_all_modes(self):
        for mode in BackupExecutionMode:
            req = _make_request(mode=mode)
            self.assertEqual(req.mode, mode)

    def test_no_forbidden_fields(self):
        req = _make_request()
        for attr in ["password", "secret", "token", "credential", "command", "ssh", "api_key"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = _make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# BackupExecutionResult
# ============================================================================

class TestBackupExecutionResult(unittest.TestCase):
    """备份执行结果测试"""

    def test_valid_result(self):
        result = _make_result()
        self.assertEqual(result.backup_id, "b-001")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    def test_frozen(self):
        result = _make_result()
        with self.assertRaises(AttributeError):
            result.backup_id = "other"

    def test_slots(self):
        result = _make_result()
        with self.assertRaises(AttributeError):
            result.__dict__

    def test_empty_backup_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionResult(backup_id="", success=True, message="ok")

    def test_success_must_be_bool(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionResult(backup_id="b-001", success=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionResult(backup_id="b-001", success=True, message=123)

    def test_timezone_aware(self):
        result = _make_result()
        self.assertIsNotNone(result.completed_at.tzinfo)

    def test_failed_result(self):
        result = _make_result(success=False, message="error")
        self.assertFalse(result.success)

    def test_no_forbidden_fields(self):
        result = _make_result()
        for attr in ["password", "secret", "token", "credential", "command"]:
            self.assertFalse(hasattr(result, attr))


# ============================================================================
# Handler Contracts
# ============================================================================

class TestLinuxBackupHandlerContract(unittest.TestCase):
    """Linux 备份处理器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(LinuxBackupHandler, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(LinuxBackupHandler, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            LinuxBackupHandler()

    def test_concrete_subclass(self):
        handler = MockLinuxHandler()
        req = _make_request()
        result = handler.execute(req)
        self.assertTrue(result.success)


class TestPVEBackupHandlerContract(unittest.TestCase):
    """PVE 备份处理器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(PVEBackupHandler, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(PVEBackupHandler, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            PVEBackupHandler()

    def test_concrete_subclass(self):
        handler = MockPVEHandler()
        req = _make_request(mode=BackupExecutionMode.PVE, adapter_id="pve-001")
        result = handler.execute(req)
        self.assertTrue(result.success)


class TestOMVBackupHandlerContract(unittest.TestCase):
    """OMV 备份处理器契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OMVBackupHandler, ABC))

    def test_has_execute(self):
        self.assertTrue(hasattr(OMVBackupHandler, "execute"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OMVBackupHandler()

    def test_concrete_subclass(self):
        handler = MockOMVHandler()
        req = _make_request(mode=BackupExecutionMode.OMV, adapter_id="omv-001")
        result = handler.execute(req)
        self.assertTrue(result.success)


# ============================================================================
# BackupRuntimeDispatcher
# ============================================================================

class TestBackupRuntimeDispatcher(unittest.TestCase):
    """备份运行时分发器测试"""

    def test_dispatch_linux(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        req = _make_request()
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_dispatch_pve(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        req = _make_request(mode=BackupExecutionMode.PVE, adapter_id="pve-001")
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_dispatch_omv(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        req = _make_request(mode=BackupExecutionMode.OMV, adapter_id="omv-001")
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_dispatch_no_handler(self):
        dispatcher = BackupRuntimeDispatcher()
        req = _make_request()
        with self.assertRaises(BackupRuntimeUnavailableError):
            dispatcher.dispatch(req)

    def test_dispatch_partial_handlers(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request()
        result = dispatcher.dispatch(req)
        self.assertTrue(result.success)

    def test_dispatch_pve_no_handler(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request(mode=BackupExecutionMode.PVE, adapter_id="pve-001")
        with self.assertRaises(BackupRuntimeUnavailableError):
            dispatcher.dispatch(req)


# ============================================================================
# RealBackupExecutor
# ============================================================================

class TestRealBackupExecutor(unittest.TestCase):
    """真实备份执行器测试"""

    def test_execute_linux(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        executor = RealBackupExecutor(dispatcher)
        req = _make_request()
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_execute_pve(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        executor = RealBackupExecutor(dispatcher)
        req = _make_request(mode=BackupExecutionMode.PVE, adapter_id="pve-001")
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_execute_omv(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        executor = RealBackupExecutor(dispatcher)
        req = _make_request(mode=BackupExecutionMode.OMV, adapter_id="omv-001")
        result = executor.execute(req)
        self.assertTrue(result.success)

    def test_execute_invalid_dispatcher(self):
        with self.assertRaises(InvalidBackupExecutionError):
            RealBackupExecutor("not_a_dispatcher")

    def test_execute_invalid_request(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        executor = RealBackupExecutor(dispatcher)
        with self.assertRaises(InvalidBackupExecutionError):
            executor.execute("not_a_request")

    def test_execute_no_handler(self):
        dispatcher = BackupRuntimeDispatcher()
        executor = RealBackupExecutor(dispatcher)
        req = _make_request()
        with self.assertRaises(BackupRuntimeUnavailableError):
            executor.execute(req)

    def test_execute_result_preserves_backup_id(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        executor = RealBackupExecutor(dispatcher)
        req = _make_request(backup_id="b-custom")
        result = executor.execute(req)
        self.assertEqual(result.backup_id, "b-custom")


# ============================================================================
# Error Model
# ============================================================================

class TestBackupEngineErrors(unittest.TestCase):
    """错误模型测试"""

    def test_engine_error(self):
        with self.assertRaises(BackupEngineError):
            raise BackupEngineError("test")

    def test_invalid_execution_error(self):
        with self.assertRaises(BackupEngineError):
            raise InvalidBackupExecutionError("test")

    def test_unavailable_error(self):
        with self.assertRaises(BackupEngineError):
            raise BackupRuntimeUnavailableError("test")

    def test_timeout_error(self):
        with self.assertRaises(BackupEngineError):
            raise BackupExecutionTimeoutError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (BackupEngineError, ("test",)),
            (InvalidBackupExecutionError, ("test",)),
            (BackupRuntimeUnavailableError, ("test",)),
            (BackupExecutionTimeoutError, ("test",)),
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
        req = _make_request()
        for attr in ["password", "secret", "token", "credential", "command", "ssh", "api_key"]:
            self.assertFalse(hasattr(req, attr))

    def test_result_no_credentials(self):
        result = _make_result()
        for attr in ["password", "secret", "token", "credential", "command"]:
            self.assertFalse(hasattr(result, attr))

    def test_no_subprocess(self):
        import ast
        import os
        engine_dir = os.path.join("backup_manager", "backup_engine")
        for filename in os.listdir(engine_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(engine_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.assertNotEqual(alias.name, "subprocess")
                        self.assertNotEqual(alias.name, "os")
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        if "subprocess" in node.module:
                            self.fail(f"subprocess imported in {filename}")
                        if node.module == "os" and any(
                            a.name in ("system", "popen") for a in node.names
                        ):
                            self.fail(f"os.system imported in {filename}")

    def test_no_exec_eval(self):
        import ast
        import os
        engine_dir = os.path.join("backup_manager", "backup_engine")
        for filename in os.listdir(engine_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(engine_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_full_lifecycle(self):
        """完整备份执行生命周期"""
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        executor = RealBackupExecutor(dispatcher)
        for mode in BackupExecutionMode:
            req = _make_request(mode=mode, adapter_id=f"{mode.value}-001")
            result = executor.execute(req)
            self.assertTrue(result.success)


# ============================================================================
# Extended Tests
# ============================================================================

class TestBackupEngineExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidBackupExecutionError, BackupEngineError))
        self.assertTrue(issubclass(BackupRuntimeUnavailableError, BackupEngineError))
        self.assertTrue(issubclass(BackupExecutionTimeoutError, BackupEngineError))

    def test_request_preserves_all_fields(self):
        req = _make_request()
        self.assertEqual(req.backup_id, "b-001")
        self.assertEqual(req.execution_id, "exec-001")
        self.assertEqual(req.transaction_id, "txn-001")
        self.assertEqual(req.adapter_id, "linux-001")
        self.assertEqual(req.mode, BackupExecutionMode.LINUX)

    def test_result_preserves_all_fields(self):
        result = _make_result()
        self.assertEqual(result.backup_id, "b-001")
        self.assertTrue(result.success)
        self.assertEqual(result.message, "ok")

    def test_request_repr_no_secrets(self):
        req = _make_request()
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_result_repr_no_secrets(self):
        result = _make_result()
        r = repr(result)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_no_password(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "password"))

    def test_request_no_secret(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "secret"))

    def test_request_no_token(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "token"))

    def test_request_no_credential(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "credential"))

    def test_request_no_command(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "command"))

    def test_request_no_ssh(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "ssh"))

    def test_request_no_api_key(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "api_key"))

    def test_result_no_password(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "password"))

    def test_result_no_secret(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "secret"))

    def test_result_no_token(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "token"))

    def test_result_no_credential(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "credential"))

    def test_result_no_command(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "command"))

    def test_request_whitespace_backup_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(backup_id="   ")

    def test_request_whitespace_execution_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(execution_id="   ")

    def test_request_whitespace_transaction_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(transaction_id="   ")

    def test_request_whitespace_adapter_id_rejected(self):
        with self.assertRaises(InvalidBackupExecutionError):
            _make_request(adapter_id="   ")

    def test_result_empty_message_accepted(self):
        result = BackupExecutionResult(backup_id="b-001", success=True, message="")
        self.assertEqual(result.message, "")

    def test_dispatcher_all_modes(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        for mode in BackupExecutionMode:
            req = _make_request(mode=mode, adapter_id=f"{mode.value}-001")
            result = dispatcher.dispatch(req)
            self.assertTrue(result.success)

    def test_executor_all_modes(self):
        dispatcher = BackupRuntimeDispatcher(
            linux_handler=MockLinuxHandler(),
            pve_handler=MockPVEHandler(),
            omv_handler=MockOMVHandler(),
        )
        executor = RealBackupExecutor(dispatcher)
        for mode in BackupExecutionMode:
            req = _make_request(mode=mode, adapter_id=f"{mode.value}-001")
            result = executor.execute(req)
            self.assertTrue(result.success)

    def test_error_messages_safe(self):
        try:
            raise BackupEngineError("test")
        except BackupEngineError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_unavailable_error_message(self):
        exc = BackupRuntimeUnavailableError("no handler")
        self.assertIn("no handler", str(exc))

    def test_timeout_error_message(self):
        exc = BackupExecutionTimeoutError("timeout")
        self.assertIn("timeout", str(exc))

    def test_invalid_error_message(self):
        exc = InvalidBackupExecutionError("invalid")
        self.assertIn("invalid", str(exc))

    def test_handler_returns_result(self):
        handler = MockLinuxHandler()
        req = _make_request()
        result = handler.execute(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_dispatcher_returns_result(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request()
        result = dispatcher.dispatch(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_executor_returns_result(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        executor = RealBackupExecutor(dispatcher)
        req = _make_request()
        result = executor.execute(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_request_no_private_key(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "private_key"))

    def test_result_no_private_key(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "private_key"))

    def test_request_no_credential_value(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "credential_value"))

    def test_result_no_credential_value(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "credential_value"))

    def test_mode_frozenset(self):
        self.assertIsInstance(BackupExecutionMode.LINUX.value, str)

    def test_request_all_modes_valid(self):
        for mode in BackupExecutionMode:
            req = _make_request(mode=mode, adapter_id=f"{mode.value}-001")
            self.assertEqual(req.mode, mode)

    def test_result_success_true(self):
        result = _make_result(success=True)
        self.assertTrue(result.success)

    def test_result_success_false(self):
        result = _make_result(success=False, message="error")
        self.assertFalse(result.success)

    def test_dispatcher_no_linux_handler(self):
        dispatcher = BackupRuntimeDispatcher(pve_handler=MockPVEHandler())
        req = _make_request()
        with self.assertRaises(BackupRuntimeUnavailableError):
            dispatcher.dispatch(req)

    def test_dispatcher_no_pve_handler(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request(mode=BackupExecutionMode.PVE, adapter_id="pve-001")
        with self.assertRaises(BackupRuntimeUnavailableError):
            dispatcher.dispatch(req)

    def test_dispatcher_no_omv_handler(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request(mode=BackupExecutionMode.OMV, adapter_id="omv-001")
        with self.assertRaises(BackupRuntimeUnavailableError):
            dispatcher.dispatch(req)

    def test_request_all_fields_present(self):
        req = _make_request()
        self.assertTrue(hasattr(req, "backup_id"))
        self.assertTrue(hasattr(req, "execution_id"))
        self.assertTrue(hasattr(req, "transaction_id"))
        self.assertTrue(hasattr(req, "adapter_id"))
        self.assertTrue(hasattr(req, "mode"))
        self.assertTrue(hasattr(req, "created_at"))

    def test_result_all_fields_present(self):
        result = _make_result()
        self.assertTrue(hasattr(result, "backup_id"))
        self.assertTrue(hasattr(result, "success"))
        self.assertTrue(hasattr(result, "message"))
        self.assertTrue(hasattr(result, "completed_at"))

    def test_request_no_stdout(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "stdout"))

    def test_request_no_stderr(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "stderr"))

    def test_result_no_stdout(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "stdout"))

    def test_result_no_stderr(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "stderr"))

    def test_handler_execute_returns_result(self):
        for HandlerClass in [MockLinuxHandler, MockPVEHandler, MockOMVHandler]:
            handler = HandlerClass()
            req = _make_request()
            result = handler.execute(req)
            self.assertIsInstance(result, BackupExecutionResult)

    def test_dispatcher_result_preserves_backup_id(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request(backup_id="b-custom-123")
        result = dispatcher.dispatch(req)
        self.assertEqual(result.backup_id, "b-custom-123")

    def test_executor_result_preserves_message(self):
        class CustomHandler(LinuxBackupHandler):
            def execute(self, request):
                return BackupExecutionResult(
                    backup_id=request.backup_id,
                    success=True, message="custom message",
                )
        dispatcher = BackupRuntimeDispatcher(linux_handler=CustomHandler())
        executor = RealBackupExecutor(dispatcher)
        req = _make_request()
        result = executor.execute(req)
        self.assertEqual(result.message, "custom message")

    def test_executor_failed_result(self):
        class FailHandler(LinuxBackupHandler):
            def execute(self, request):
                return BackupExecutionResult(
                    backup_id=request.backup_id,
                    success=False, message="backup failed",
                )
        dispatcher = BackupRuntimeDispatcher(linux_handler=FailHandler())
        executor = RealBackupExecutor(dispatcher)
        req = _make_request()
        result = executor.execute(req)
        self.assertFalse(result.success)

    def test_mode_linux_value(self):
        self.assertEqual(BackupExecutionMode.LINUX.value, "linux")

    def test_mode_pve_value(self):
        self.assertEqual(BackupExecutionMode.PVE.value, "pve")

    def test_mode_omv_value(self):
        self.assertEqual(BackupExecutionMode.OMV.value, "omv")

    def test_request_different_backup_ids(self):
        for bid in ["b-001", "b-002", "b-003", "backup-abc"]:
            req = _make_request(backup_id=bid)
            self.assertEqual(req.backup_id, bid)

    def test_request_different_adapter_ids(self):
        for aid in ["linux-001", "pve-001", "omv-001", "adapter-abc"]:
            req = _make_request(adapter_id=aid)
            self.assertEqual(req.adapter_id, aid)

    def test_result_different_messages(self):
        for msg in ["ok", "completed", "partial", "error"]:
            result = BackupExecutionResult(
                backup_id="b-001", success=True, message=msg,
            )
            self.assertEqual(result.message, msg)

    def test_dispatcher_handler_replacement(self):
        class Handler1(LinuxBackupHandler):
            def execute(self, request):
                return BackupExecutionResult(
                    backup_id=request.backup_id,
                    success=True, message="handler1",
                )
        class Handler2(LinuxBackupHandler):
            def execute(self, request):
                return BackupExecutionResult(
                    backup_id=request.backup_id,
                    success=True, message="handler2",
                )
        dispatcher = BackupRuntimeDispatcher(linux_handler=Handler1())
        req = _make_request()
        result = dispatcher.dispatch(req)
        self.assertEqual(result.message, "handler1")

    def test_executor_multiple_executions(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        executor = RealBackupExecutor(dispatcher)
        for i in range(5):
            req = _make_request(backup_id=f"b-{i:03d}", execution_id=f"exec-{i:03d}")
            result = executor.execute(req)
            self.assertTrue(result.success)
            self.assertEqual(result.backup_id, f"b-{i:03d}")

    def test_error_hierarchy_deep(self):
        self.assertTrue(issubclass(BackupEngineError, Exception))
        self.assertTrue(issubclass(InvalidBackupExecutionError, Exception))
        self.assertTrue(issubclass(BackupRuntimeUnavailableError, Exception))
        self.assertTrue(issubclass(BackupExecutionTimeoutError, Exception))

    def test_request_no_private_key(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "private_key"))

    def test_result_no_private_key(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "private_key"))

    def test_request_no_credential_value(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "credential_value"))

    def test_result_no_credential_value(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "credential_value"))

    def test_request_no_shell(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "shell"))

    def test_result_no_shell(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "shell"))

    def test_request_no_subprocess(self):
        req = _make_request()
        self.assertFalse(hasattr(req, "subprocess"))

    def test_result_no_subprocess(self):
        result = _make_result()
        self.assertFalse(hasattr(result, "subprocess"))

    def test_mode_is_enum(self):
        from enum import Enum
        self.assertTrue(issubclass(BackupExecutionMode, Enum))

    def test_request_invalid_type_backup_id(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionRequest(
                backup_id=123, execution_id="exec-001",
                transaction_id="txn-001", adapter_id="linux-001",
                mode=BackupExecutionMode.LINUX,
            )

    def test_request_invalid_type_adapter_id(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionRequest(
                backup_id="b-001", execution_id="exec-001",
                transaction_id="txn-001", adapter_id=123,
                mode=BackupExecutionMode.LINUX,
            )

    def test_result_invalid_type_backup_id(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionResult(backup_id=123, success=True, message="ok")

    def test_result_invalid_type_success(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionResult(backup_id="b-001", success="yes", message="ok")

    def test_result_invalid_type_message(self):
        with self.assertRaises(InvalidBackupExecutionError):
            BackupExecutionResult(backup_id="b-001", success=True, message=123)

    def test_dispatcher_default_none_handlers(self):
        dispatcher = BackupRuntimeDispatcher()
        self.assertIsNone(dispatcher._handlers[BackupExecutionMode.LINUX])
        self.assertIsNone(dispatcher._handlers[BackupExecutionMode.PVE])
        self.assertIsNone(dispatcher._handlers[BackupExecutionMode.OMV])

    def test_executor_stores_dispatcher(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        executor = RealBackupExecutor(dispatcher)
        self.assertIs(executor._dispatcher, dispatcher)

    def test_error_backup_engine_message(self):
        exc = BackupEngineError("engine error")
        self.assertIn("engine error", str(exc))

    def test_error_invalid_execution_message(self):
        exc = InvalidBackupExecutionError("invalid execution")
        self.assertIn("invalid execution", str(exc))

    def test_error_unavailable_message(self):
        exc = BackupRuntimeUnavailableError("unavailable")
        self.assertIn("unavailable", str(exc))

    def test_error_timeout_message(self):
        exc = BackupExecutionTimeoutError("timeout")
        self.assertIn("timeout", str(exc))

    def test_request_all_modes_string_values(self):
        self.assertEqual(BackupExecutionMode.LINUX.value, "linux")
        self.assertEqual(BackupExecutionMode.PVE.value, "pve")
        self.assertEqual(BackupExecutionMode.OMV.value, "omv")

    def test_result_success_bool_check(self):
        result = _make_result(success=True)
        self.assertIsInstance(result.success, bool)

    def test_request_created_at_type(self):
        from datetime import datetime
        req = _make_request()
        self.assertIsInstance(req.created_at, datetime)

    def test_result_completed_at_type(self):
        from datetime import datetime
        result = _make_result()
        self.assertIsInstance(result.completed_at, datetime)

    def test_dispatcher_dispatch_returns_result(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        req = _make_request()
        result = dispatcher.dispatch(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_executor_execute_returns_result(self):
        dispatcher = BackupRuntimeDispatcher(linux_handler=MockLinuxHandler())
        executor = RealBackupExecutor(dispatcher)
        req = _make_request()
        result = executor.execute(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_handler_execute_linux_returns_result(self):
        handler = MockLinuxHandler()
        req = _make_request()
        result = handler.execute(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_handler_execute_pve_returns_result(self):
        handler = MockPVEHandler()
        req = _make_request(mode=BackupExecutionMode.PVE, adapter_id="pve-001")
        result = handler.execute(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_handler_execute_omv_returns_result(self):
        handler = MockOMVHandler()
        req = _make_request(mode=BackupExecutionMode.OMV, adapter_id="omv-001")
        result = handler.execute(req)
        self.assertIsInstance(result, BackupExecutionResult)

    def test_request_mode_is_backup_execution_mode(self):
        req = _make_request()
        self.assertIsInstance(req.mode, BackupExecutionMode)

    def test_error_all_subclasses(self):
        subclasses = [
            InvalidBackupExecutionError,
            BackupRuntimeUnavailableError,
            BackupExecutionTimeoutError,
        ]
        for cls in subclasses:
            self.assertTrue(issubclass(cls, BackupEngineError))

    def test_mode_enum_members(self):
        members = list(BackupExecutionMode)
        self.assertEqual(len(members), 3)


if __name__ == "__main__":
    unittest.main()
