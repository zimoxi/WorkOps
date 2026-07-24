"""
WorkOps Adapter Execution Context Tests
Sprint051: Adapter Execution Context Foundation

覆盖：
- ExecutionMode enum
- ExecutionMetadata validation
- ExecutionContext validation
- AdapterRuntimeContext contract
- validate_execution_context helper
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.runtime_context.model import ExecutionMode
from backup_manager.runtime_context.metadata import ExecutionMetadata
from backup_manager.runtime_context.context import (
    ExecutionContext,
    AdapterRuntimeContext,
    validate_execution_context,
)
from backup_manager.runtime_context.errors import (
    ExecutionContextError,
    InvalidExecutionContextError,
    ExecutionContextConflictError,
)
from backup_manager.credentials.binding_model import CredentialType, CredentialReference


# ============================================================================
# ExecutionMode
# ============================================================================

class TestExecutionMode(unittest.TestCase):
    """执行模式测试"""

    def test_read_only(self):
        self.assertEqual(ExecutionMode.READ_ONLY.value, "read_only")

    def test_mutation(self):
        self.assertEqual(ExecutionMode.MUTATION.value, "mutation")

    def test_two_modes(self):
        self.assertEqual(len(ExecutionMode), 2)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            ExecutionMode("nonexistent")


# ============================================================================
# ExecutionMetadata
# ============================================================================

class TestExecutionMetadata(unittest.TestCase):
    """执行元数据测试"""

    def _make_metadata(self, **kwargs):
        defaults = {
            "execution_id": "exec-001",
            "operation_id": "op-001",
            "adapter_id": "linux-001",
        }
        defaults.update(kwargs)
        return ExecutionMetadata(**defaults)

    def test_valid_metadata(self):
        meta = self._make_metadata()
        self.assertEqual(meta.execution_id, "exec-001")
        self.assertEqual(meta.operation_id, "op-001")
        self.assertEqual(meta.adapter_id, "linux-001")

    def test_frozen(self):
        meta = self._make_metadata()
        with self.assertRaises(AttributeError):
            meta.execution_id = "other"

    def test_slots(self):
        meta = self._make_metadata()
        with self.assertRaises(AttributeError):
            meta.__dict__

    def test_empty_execution_id_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            self._make_metadata(execution_id="")

    def test_empty_operation_id_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            self._make_metadata(operation_id="")

    def test_empty_adapter_id_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            self._make_metadata(adapter_id="")

    def test_timezone_aware(self):
        meta = self._make_metadata()
        self.assertIsNotNone(meta.created_at.tzinfo)

    def test_no_forbidden_fields(self):
        meta = self._make_metadata()
        for attr in ["password", "credential", "secret", "token", "ssh", "command", "stdout", "stderr"]:
            self.assertFalse(hasattr(meta, attr))

    def test_repr_no_secrets(self):
        meta = self._make_metadata()
        r = repr(meta)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# ExecutionContext
# ============================================================================

class TestExecutionContext(unittest.TestCase):
    """执行上下文测试"""

    def _make_context(self, **kwargs):
        meta = ExecutionMetadata(
            execution_id="exec-001",
            operation_id="op-001",
            adapter_id="linux-001",
        )
        defaults = {"metadata": meta, "mode": ExecutionMode.READ_ONLY}
        defaults.update(kwargs)
        return ExecutionContext(**defaults)

    def test_valid_context(self):
        ctx = self._make_context()
        self.assertEqual(ctx.metadata.execution_id, "exec-001")
        self.assertEqual(ctx.mode, ExecutionMode.READ_ONLY)
        self.assertIsNone(ctx.credential_reference)

    def test_frozen(self):
        ctx = self._make_context()
        with self.assertRaises(AttributeError):
            ctx.mode = ExecutionMode.MUTATION

    def test_slots(self):
        ctx = self._make_context()
        with self.assertRaises(AttributeError):
            ctx.__dict__

    def test_invalid_metadata_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            ExecutionContext(metadata="bad", mode=ExecutionMode.READ_ONLY)

    def test_invalid_mode_rejected(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        with self.assertRaises(InvalidExecutionContextError):
            ExecutionContext(metadata=meta, mode="read_only")

    def test_with_credential_reference(self):
        ref = CredentialReference(
            credential_id="cred-001",
            credential_type=CredentialType.SSH,
            provider="vault",
        )
        ctx = self._make_context(credential_reference=ref)
        self.assertIsNotNone(ctx.credential_reference)
        self.assertEqual(ctx.credential_reference.credential_id, "cred-001")

    def test_invalid_credential_reference_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            self._make_context(credential_reference="not_a_ref")

    def test_mutation_mode(self):
        ctx = self._make_context(mode=ExecutionMode.MUTATION)
        self.assertEqual(ctx.mode, ExecutionMode.MUTATION)

    def test_no_forbidden_fields(self):
        ctx = self._make_context()
        for attr in ["password", "secret", "token", "private_key", "credential_value"]:
            self.assertFalse(hasattr(ctx, attr))


# ============================================================================
# AdapterRuntimeContext Contract
# ============================================================================

class TestAdapterRuntimeContextContract(unittest.TestCase):
    """适配器运行时上下文契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(AdapterRuntimeContext, ABC))

    def test_has_create(self):
        self.assertTrue(hasattr(AdapterRuntimeContext, "create"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            AdapterRuntimeContext()

    def test_concrete_subclass(self):
        class MockContext(AdapterRuntimeContext):
            def create(self, metadata, mode, credential_reference):
                return ExecutionContext(
                    metadata=metadata, mode=mode,
                    credential_reference=credential_reference,
                )
        ctx_factory = MockContext()
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ctx_factory.create(meta, ExecutionMode.READ_ONLY, None)
        self.assertEqual(ctx.metadata.execution_id, "exec-001")

    def test_missing_create(self):
        class BadContext(AdapterRuntimeContext):
            pass
        with self.assertRaises(TypeError):
            BadContext()


# ============================================================================
# validate_execution_context
# ============================================================================

class TestValidateExecutionContext(unittest.TestCase):
    """验证执行上下文测试"""

    def test_valid_context(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        # Should not raise
        validate_execution_context(ctx)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            validate_execution_context("not_a_context")

    def test_with_credential_ref(self):
        ref = CredentialReference(
            credential_id="cred-001", credential_type=CredentialType.SSH, provider="vault",
        )
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY, credential_reference=ref)
        validate_execution_context(ctx)


# ============================================================================
# Error Model
# ============================================================================

class TestExecutionContextErrors(unittest.TestCase):
    """错误模型测试"""

    def test_context_error(self):
        with self.assertRaises(ExecutionContextError):
            raise ExecutionContextError("test")

    def test_invalid_context_error(self):
        with self.assertRaises(ExecutionContextError):
            raise InvalidExecutionContextError("test")

    def test_conflict_error(self):
        with self.assertRaises(ExecutionContextError):
            raise ExecutionContextConflictError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (ExecutionContextError, ("test",)),
            (InvalidExecutionContextError, ("test",)),
            (ExecutionContextConflictError, ("test",)),
        ]:
            msg = str(exc_cls(*args))
            for term in ["password", "secret", "token", "credential", "ssh"]:
                self.assertNotIn(term, msg.lower())


# ============================================================================
# Security Boundary
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_metadata_no_credentials(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(meta, attr))

    def test_context_no_credentials(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        for attr in ["password", "secret", "token", "private_key", "credential_value"]:
            self.assertFalse(hasattr(ctx, attr))

    def test_no_subprocess(self):
        import ast
        import os
        rc_dir = os.path.join("backup_manager", "runtime_context")
        for filename in os.listdir(rc_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(rc_dir, filename)
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
        rc_dir = os.path.join("backup_manager", "runtime_context")
        for filename in os.listdir(rc_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(rc_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_context_lifecycle(self):
        """完整上下文生命周期"""
        class MockContext(AdapterRuntimeContext):
            def create(self, metadata, mode, credential_reference):
                return ExecutionContext(
                    metadata=metadata, mode=mode,
                    credential_reference=credential_reference,
                )
        ctx_factory = MockContext()
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ref = CredentialReference(
            credential_id="cred-001", credential_type=CredentialType.SSH, provider="vault",
        )
        ctx = ctx_factory.create(meta, ExecutionMode.READ_ONLY, ref)
        self.assertEqual(ctx.metadata.execution_id, "exec-001")
        self.assertEqual(ctx.mode, ExecutionMode.READ_ONLY)
        self.assertEqual(ctx.credential_reference.credential_id, "cred-001")
        validate_execution_context(ctx)


# ============================================================================
# Extended Tests
# ============================================================================

class TestExecutionContextExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidExecutionContextError, ExecutionContextError))
        self.assertTrue(issubclass(ExecutionContextConflictError, ExecutionContextError))

    def test_metadata_repr_no_secrets(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        r = repr(meta)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_context_repr_no_secrets(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        r = repr(ctx)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_read_only_mode_context(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        self.assertEqual(ctx.mode, ExecutionMode.READ_ONLY)

    def test_mutation_mode_context(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.MUTATION)
        self.assertEqual(ctx.mode, ExecutionMode.MUTATION)

    def test_metadata_preserved_in_context(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        self.assertIs(ctx.metadata, meta)

    def test_credential_ref_preserved(self):
        ref = CredentialReference(
            credential_id="cred-001", credential_type=CredentialType.SSH, provider="vault",
        )
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY, credential_reference=ref)
        self.assertIs(ctx.credential_reference, ref)

    def test_error_messages_safe(self):
        try:
            raise ExecutionContextError("test")
        except ExecutionContextError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_context_no_command(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        self.assertFalse(hasattr(ctx, "command"))

    def test_context_no_ssh(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        self.assertFalse(hasattr(ctx, "ssh"))

    def test_metadata_whitespace_id_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            ExecutionMetadata(execution_id="   ", operation_id="op-001", adapter_id="linux-001")

    def test_metadata_whitespace_operation_id_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            ExecutionMetadata(execution_id="exec-001", operation_id="   ", adapter_id="linux-001")

    def test_metadata_whitespace_adapter_id_rejected(self):
        with self.assertRaises(InvalidExecutionContextError):
            ExecutionMetadata(execution_id="exec-001", operation_id="op-001", adapter_id="   ")

    def test_context_all_modes(self):
        for mode in ExecutionMode:
            meta = ExecutionMetadata(
                execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
            )
            ctx = ExecutionContext(metadata=meta, mode=mode)
            self.assertEqual(ctx.mode, mode)

    def test_context_with_api_token_ref(self):
        ref = CredentialReference(
            credential_id="cred-001", credential_type=CredentialType.API_TOKEN, provider="vault",
        )
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY, credential_reference=ref)
        self.assertEqual(ctx.credential_reference.credential_type, CredentialType.API_TOKEN)

    def test_context_with_password_ref(self):
        ref = CredentialReference(
            credential_id="cred-001", credential_type=CredentialType.PASSWORD, provider="vault",
        )
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY, credential_reference=ref)
        self.assertEqual(ctx.credential_reference.credential_type, CredentialType.PASSWORD)

    def test_adapter_runtime_context_returns_context(self):
        class MockContext(AdapterRuntimeContext):
            def create(self, metadata, mode, credential_reference):
                return ExecutionContext(
                    metadata=metadata, mode=mode,
                    credential_reference=credential_reference,
                )
        ctx_factory = MockContext()
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ctx_factory.create(meta, ExecutionMode.READ_ONLY, None)
        self.assertIsInstance(ctx, ExecutionContext)

    def test_error_messages_safe_all(self):
        try:
            raise InvalidExecutionContextError("test")
        except InvalidExecutionContextError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_context_conflict_error_message(self):
        exc = ExecutionContextConflictError("conflict")
        self.assertIn("conflict", str(exc))

    def test_metadata_all_fields(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        self.assertEqual(meta.execution_id, "exec-001")
        self.assertEqual(meta.operation_id, "op-001")
        self.assertEqual(meta.adapter_id, "linux-001")
        self.assertIsNotNone(meta.created_at)

    def test_context_none_credential_default(self):
        meta = ExecutionMetadata(
            execution_id="exec-001", operation_id="op-001", adapter_id="linux-001",
        )
        ctx = ExecutionContext(metadata=meta, mode=ExecutionMode.READ_ONLY)
        self.assertIsNone(ctx.credential_reference)


if __name__ == "__main__":
    unittest.main()
