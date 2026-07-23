"""
WorkOps Unified Operation API Tests
Sprint045: Unified Operation API Foundation

覆盖：
- OperationRequestModel validation
- OperationResponseModel validation
- OperationGateway contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.operations.operation import OperationType
from backup_manager.api.request import OperationRequestModel
from backup_manager.api.response import OperationResponseModel
from backup_manager.api.gateway import OperationGateway
from backup_manager.api.errors import (
    OperationAPIError,
    InvalidOperationRequestError,
    OperationSubmissionError,
    OperationUnavailableError,
)


# ============================================================================
# OperationRequestModel
# ============================================================================

class TestOperationRequestModel(unittest.TestCase):
    """操作请求模型测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "request_id": "req-001",
            "operation_type": OperationType.BACKUP,
        }
        defaults.update(kwargs)
        return OperationRequestModel(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.request_id, "req-001")
        self.assertEqual(req.operation_type, OperationType.BACKUP)

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.request_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidOperationRequestError):
            self._make_request(request_id="")

    def test_invalid_operation_type_rejected(self):
        with self.assertRaises(InvalidOperationRequestError):
            self._make_request(operation_type="backup")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_device_id_none_default(self):
        req = self._make_request()
        self.assertIsNone(req.device_id)

    def test_with_device_id(self):
        req = self._make_request(device_id="dev-001")
        self.assertEqual(req.device_id, "dev-001")

    def test_all_operation_types(self):
        for op_type in OperationType:
            req = self._make_request(operation_type=op_type)
            self.assertEqual(req.operation_type, op_type)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "secret_ref", "token",
                      "ssh", "command", "ip", "hostname"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# OperationResponseModel
# ============================================================================

class TestOperationResponseModel(unittest.TestCase):
    """操作响应模型测试"""

    def test_valid_response(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        self.assertEqual(resp.request_id, "req-001")
        self.assertTrue(resp.accepted)

    def test_frozen(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            resp.request_id = "other"

    def test_slots(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        with self.assertRaises(AttributeError):
            resp.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidOperationRequestError):
            OperationResponseModel(request_id="", accepted=True, message="ok")

    def test_accepted_must_be_bool(self):
        with self.assertRaises(InvalidOperationRequestError):
            OperationResponseModel(request_id="req-001", accepted=1, message="ok")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidOperationRequestError):
            OperationResponseModel(request_id="req-001", accepted=True, message=123)

    def test_timezone_aware(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        self.assertIsNotNone(resp.created_at.tzinfo)

    def test_operation_id_none_default(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        self.assertIsNone(resp.operation_id)

    def test_with_operation_id(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
            operation_id="op-001",
        )
        self.assertEqual(resp.operation_id, "op-001")

    def test_rejected_response(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=False, message="denied",
        )
        self.assertFalse(resp.accepted)

    def test_no_forbidden_fields(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        for attr in ["secret", "credential", "password", "token", "command"]:
            self.assertFalse(hasattr(resp, attr))


# ============================================================================
# OperationGateway Contract
# ============================================================================

class TestOperationGatewayContract(unittest.TestCase):
    """操作网关契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OperationGateway, ABC))

    def test_has_submit(self):
        self.assertTrue(hasattr(OperationGateway, "submit"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OperationGateway()

    def test_concrete_subclass(self):
        class MockGateway(OperationGateway):
            def submit(self, request):
                return OperationResponseModel(
                    request_id=request.request_id,
                    accepted=True, message="ok",
                    operation_id="op-001",
                )
        gateway = MockGateway()
        req = OperationRequestModel(
            request_id="req-001", operation_type=OperationType.BACKUP,
        )
        resp = gateway.submit(req)
        self.assertTrue(resp.accepted)
        self.assertEqual(resp.operation_id, "op-001")

    def test_missing_submit(self):
        class BadGateway(OperationGateway):
            pass
        with self.assertRaises(TypeError):
            BadGateway()


# ============================================================================
# Error Model
# ============================================================================

class TestOperationAPIErrors(unittest.TestCase):
    """错误模型测试"""

    def test_api_error(self):
        with self.assertRaises(OperationAPIError):
            raise OperationAPIError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(OperationAPIError):
            raise InvalidOperationRequestError("test")

    def test_submission_error(self):
        with self.assertRaises(OperationAPIError):
            raise OperationSubmissionError("test")

    def test_unavailable_error(self):
        with self.assertRaises(OperationAPIError):
            raise OperationUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (OperationAPIError, ("test",)),
            (InvalidOperationRequestError, ("test",)),
            (OperationSubmissionError, ("test",)),
            (OperationUnavailableError, ("test",)),
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
        req = OperationRequestModel(
            request_id="req-001", operation_type=OperationType.BACKUP,
        )
        for attr in ["password", "credential", "secret", "token", "ssh", "command"]:
            self.assertFalse(hasattr(req, attr))

    def test_response_no_credentials(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        for attr in ["secret", "credential", "password", "token", "command"]:
            self.assertFalse(hasattr(resp, attr))

    def test_no_subprocess(self):
        import ast
        import os
        api_dir = os.path.join("backup_manager", "api")
        for filename in os.listdir(api_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(api_dir, filename)
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
        api_dir = os.path.join("backup_manager", "api")
        for filename in os.listdir(api_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(api_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_gateway_lifecycle(self):
        """完整网关生命周期"""
        class MockGateway(OperationGateway):
            def submit(self, request):
                return OperationResponseModel(
                    request_id=request.request_id,
                    accepted=True, message="ok",
                    operation_id="op-001",
                )
        gateway = MockGateway()
        req = OperationRequestModel(
            request_id="req-001", operation_type=OperationType.BACKUP,
        )
        resp = gateway.submit(req)
        self.assertTrue(resp.accepted)
        self.assertEqual(resp.operation_id, "op-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestOperationAPIExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidOperationRequestError, OperationAPIError))
        self.assertTrue(issubclass(OperationSubmissionError, OperationAPIError))
        self.assertTrue(issubclass(OperationUnavailableError, OperationAPIError))

    def test_request_repr_no_secrets(self):
        req = OperationRequestModel(
            request_id="req-001", operation_type=OperationType.BACKUP,
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_response_repr_no_secrets(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
        )
        r = repr(resp)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_gateway_rejected_response(self):
        class RejectGateway(OperationGateway):
            def submit(self, request):
                return OperationResponseModel(
                    request_id=request.request_id,
                    accepted=False, message="denied by policy",
                )
        gateway = RejectGateway()
        req = OperationRequestModel(
            request_id="req-001", operation_type=OperationType.BACKUP,
        )
        resp = gateway.submit(req)
        self.assertFalse(resp.accepted)
        self.assertIn("denied", resp.message)

    def test_request_all_operation_types(self):
        for op_type in OperationType:
            req = OperationRequestModel(
                request_id=f"req-{op_type.value}", operation_type=op_type,
            )
            self.assertEqual(req.operation_type, op_type)

    def test_response_with_all_fields(self):
        resp = OperationResponseModel(
            request_id="req-001", accepted=True, message="ok",
            operation_id="op-001",
        )
        self.assertEqual(resp.request_id, "req-001")
        self.assertTrue(resp.accepted)
        self.assertEqual(resp.message, "ok")
        self.assertEqual(resp.operation_id, "op-001")

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidOperationRequestError):
            OperationRequestModel(request_id="   ", operation_type=OperationType.BACKUP)

    def test_response_whitespace_id_rejected(self):
        with self.assertRaises(InvalidOperationRequestError):
            OperationResponseModel(request_id="   ", accepted=True, message="ok")

    def test_error_messages_safe(self):
        try:
            raise OperationAPIError("test")
        except OperationAPIError as e:
            msg = str(e)
            for term in ["password", "secret", "token"]:
                self.assertNotIn(term, msg.lower())

    def test_submission_error_message(self):
        exc = OperationSubmissionError("submit failed")
        self.assertIn("submit failed", str(exc))

    def test_unavailable_error_message(self):
        exc = OperationUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_gateway_returns_response(self):
        class MockGateway(OperationGateway):
            def submit(self, request):
                return OperationResponseModel(
                    request_id=request.request_id,
                    accepted=True, message="ok",
                )
        gateway = MockGateway()
        req = OperationRequestModel(
            request_id="req-001", operation_type=OperationType.HEALTH_CHECK,
        )
        resp = gateway.submit(req)
        self.assertIsInstance(resp, OperationResponseModel)

    def test_response_empty_message_accepted(self):
        resp = OperationResponseModel(request_id="req-001", accepted=True, message="")
        self.assertEqual(resp.message, "")


if __name__ == "__main__":
    unittest.main()
