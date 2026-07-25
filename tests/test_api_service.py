"""
WorkOps API Service Layer Tests
Sprint064: API Service Layer Foundation

覆盖：
- APIRequestType enum
- APIRequest validation
- APIResponseStatus enum
- APIResponse validation
- OperationService contract
- validate_api_request
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.api.v1_request import APIRequestType, APIRequest, validate_api_request
from backup_manager.api.v1_response import APIResponseStatus, APIResponse
from backup_manager.api.v1_service import OperationService
from backup_manager.api.v1_errors import (
    APIError,
    InvalidAPIRequestError,
    APIServiceUnavailableError,
    APIResponseError,
)


# ============================================================================
# APIRequestType
# ============================================================================

class TestAPIRequestType(unittest.TestCase):
    """API 请求类型测试"""

    def test_backup(self):
        self.assertEqual(APIRequestType.BACKUP.value, "backup")

    def test_restore(self):
        self.assertEqual(APIRequestType.RESTORE.value, "restore")

    def test_health(self):
        self.assertEqual(APIRequestType.HEALTH.value, "health")

    def test_status(self):
        self.assertEqual(APIRequestType.STATUS.value, "status")

    def test_four_types(self):
        self.assertEqual(len(APIRequestType), 4)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            APIRequestType("nonexistent")


# ============================================================================
# APIRequest
# ============================================================================

class TestAPIRequest(unittest.TestCase):
    """API 请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "request_id": "req-001",
            "request_type": APIRequestType.BACKUP,
            "resource_id": "res-001",
        }
        defaults.update(kwargs)
        return APIRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.request_id, "req-001")
        self.assertEqual(req.request_type, APIRequestType.BACKUP)
        self.assertEqual(req.resource_id, "res-001")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.request_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            self._make_request(request_id="")

    def test_invalid_request_type_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            self._make_request(request_type="backup")

    def test_empty_resource_id_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            self._make_request(resource_id="")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_all_request_types(self):
        for rt in APIRequestType:
            req = self._make_request(request_type=rt)
            self.assertEqual(req.request_type, rt)

    def test_no_forbidden_fields(self):
        req = self._make_request()
        for attr in ["password", "credential", "secret", "token", "command", "ssh"]:
            self.assertFalse(hasattr(req, attr))

    def test_repr_no_secrets(self):
        req = self._make_request()
        r = repr(req)
        for term in ["password", "secret", "token", "credential"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# APIResponseStatus
# ============================================================================

class TestAPIResponseStatus(unittest.TestCase):
    """API 响应状态测试"""

    def test_success(self):
        self.assertEqual(APIResponseStatus.SUCCESS.value, "success")

    def test_failed(self):
        self.assertEqual(APIResponseStatus.FAILED.value, "failed")

    def test_rejected(self):
        self.assertEqual(APIResponseStatus.REJECTED.value, "rejected")

    def test_three_statuses(self):
        self.assertEqual(len(APIResponseStatus), 3)

    def test_invalid_rejected(self):
        with self.assertRaises(ValueError):
            APIResponseStatus("nonexistent")


# ============================================================================
# APIResponse
# ============================================================================

class TestAPIResponse(unittest.TestCase):
    """API 响应测试"""

    def test_valid_response(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertEqual(resp.request_id, "req-001")
        self.assertEqual(resp.status, APIResponseStatus.SUCCESS)
        self.assertEqual(resp.message, "ok")

    def test_frozen(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        with self.assertRaises(AttributeError):
            resp.request_id = "other"

    def test_slots(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        with self.assertRaises(AttributeError):
            resp.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            APIResponse(
                request_id="", status=APIResponseStatus.SUCCESS,
                message="ok",
            )

    def test_invalid_status_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            APIResponse(
                request_id="req-001", status="success",
                message="ok",
            )

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidAPIRequestError):
            APIResponse(
                request_id="req-001", status=APIResponseStatus.SUCCESS,
                message=123,
            )

    def test_timezone_aware(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertIsNotNone(resp.created_at.tzinfo)

    def test_all_statuses(self):
        for status in APIResponseStatus:
            resp = APIResponse(
                request_id="req-001", status=status,
                message="ok",
            )
            self.assertEqual(resp.status, status)

    def test_no_forbidden_fields(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        for attr in ["password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(resp, attr))

    def test_repr_no_secrets(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        r = repr(resp)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# OperationService Contract
# ============================================================================

class TestOperationServiceContract(unittest.TestCase):
    """操作服务契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(OperationService, ABC))

    def test_has_handle(self):
        self.assertTrue(hasattr(OperationService, "handle"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            OperationService()

    def test_concrete_subclass(self):
        class MockService(OperationService):
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.SUCCESS,
                    message="ok",
                )
        service = MockService()
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        resp = service.handle(req)
        self.assertEqual(resp.status, APIResponseStatus.SUCCESS)

    def test_missing_handle(self):
        class BadService(OperationService):
            pass
        with self.assertRaises(TypeError):
            BadService()


# ============================================================================
# validate_api_request
# ============================================================================

class TestValidateAPIRequest(unittest.TestCase):
    """验证 API 请求测试"""

    def test_valid_request(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        validate_api_request(req)

    def test_invalid_type_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            validate_api_request("not_a_request")


# ============================================================================
# Error Model
# ============================================================================

class TestAPIErrors(unittest.TestCase):
    """错误模型测试"""

    def test_api_error(self):
        with self.assertRaises(APIError):
            raise APIError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(APIError):
            raise InvalidAPIRequestError("test")

    def test_service_unavailable_error(self):
        with self.assertRaises(APIError):
            raise APIServiceUnavailableError("test")

    def test_response_error(self):
        with self.assertRaises(APIError):
            raise APIResponseError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (APIError, ("test",)),
            (InvalidAPIRequestError, ("test",)),
            (APIServiceUnavailableError, ("test",)),
            (APIResponseError, ("test",)),
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
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        for attr in ["password", "credential", "secret", "token", "command", "ssh"]:
            self.assertFalse(hasattr(req, attr))

    def test_response_no_credentials(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        for attr in ["password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(resp, attr))

    def test_no_subprocess(self):
        import ast
        import os
        for filename in ["v1_request.py", "v1_response.py", "v1_service.py", "v1_errors.py"]:
            filepath = os.path.join("backup_manager", "api", filename)
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
        for filename in ["v1_request.py", "v1_response.py", "v1_service.py", "v1_errors.py"]:
            filepath = os.path.join("backup_manager", "api", filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_service_lifecycle(self):
        """完整服务生命周期"""
        class MockService(OperationService):
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.SUCCESS,
                    message="ok",
                )
        service = MockService()
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        resp = service.handle(req)
        self.assertEqual(resp.status, APIResponseStatus.SUCCESS)
        self.assertEqual(resp.request_id, "req-001")


# ============================================================================
# Extended Tests
# ============================================================================

class TestAPIServiceExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidAPIRequestError, APIError))
        self.assertTrue(issubclass(APIServiceUnavailableError, APIError))
        self.assertTrue(issubclass(APIResponseError, APIError))

    def test_request_repr_no_secrets(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_response_repr_no_secrets(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        r = repr(resp)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_preserves_all_fields(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertEqual(req.request_id, "req-001")
        self.assertEqual(req.request_type, APIRequestType.BACKUP)
        self.assertEqual(req.resource_id, "res-001")

    def test_response_preserves_all_fields(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertEqual(resp.request_id, "req-001")
        self.assertEqual(resp.status, APIResponseStatus.SUCCESS)
        self.assertEqual(resp.message, "ok")

    def test_service_returns_response(self):
        class MockService(OperationService):
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.SUCCESS,
                    message="ok",
                )
        service = MockService()
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        resp = service.handle(req)
        self.assertIsInstance(resp, APIResponse)

    def test_service_failed_response(self):
        class MockService(OperationService):
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.FAILED,
                    message="error",
                )
        service = MockService()
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        resp = service.handle(req)
        self.assertEqual(resp.status, APIResponseStatus.FAILED)

    def test_service_rejected_response(self):
        class MockService(OperationService):
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.REJECTED,
                    message="denied",
                )
        service = MockService()
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        resp = service.handle(req)
        self.assertEqual(resp.status, APIResponseStatus.REJECTED)

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            APIRequest(
                request_id="   ", request_type=APIRequestType.BACKUP,
                resource_id="res-001",
            )

    def test_request_whitespace_resource_id_rejected(self):
        with self.assertRaises(InvalidAPIRequestError):
            APIRequest(
                request_id="req-001", request_type=APIRequestType.BACKUP,
                resource_id="   ",
            )

    def test_response_empty_message_accepted(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="",
        )
        self.assertEqual(resp.message, "")

    def test_request_no_password(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "password"))

    def test_request_no_secret(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "secret"))

    def test_request_no_token(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "token"))

    def test_request_no_command(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "command"))

    def test_response_no_password(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertFalse(hasattr(resp, "password"))

    def test_response_no_secret(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertFalse(hasattr(resp, "secret"))

    def test_response_no_token(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertFalse(hasattr(resp, "token"))

    def test_response_no_command(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertFalse(hasattr(resp, "command"))

    def test_error_messages_safe(self):
        try:
            raise APIError("test")
        except APIError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_unavailable_error_message(self):
        exc = APIServiceUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_response_error_message(self):
        exc = APIResponseError("response error")
        self.assertIn("response error", str(exc))

    def test_request_all_fields_present(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertTrue(hasattr(req, "request_id"))
        self.assertTrue(hasattr(req, "request_type"))
        self.assertTrue(hasattr(req, "resource_id"))
        self.assertTrue(hasattr(req, "created_at"))

    def test_response_all_fields_present(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertTrue(hasattr(resp, "request_id"))
        self.assertTrue(hasattr(resp, "status"))
        self.assertTrue(hasattr(resp, "message"))
        self.assertTrue(hasattr(resp, "created_at"))

    def test_request_no_credential(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "credential"))

    def test_request_no_ssh(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "ssh"))

    def test_response_no_credential(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertFalse(hasattr(resp, "credential"))

    def test_service_all_request_types(self):
        class MockService(OperationService):
            def handle(self, request):
                return APIResponse(
                    request_id=request.request_id,
                    status=APIResponseStatus.SUCCESS,
                    message="ok",
                )
        service = MockService()
        for rt in APIRequestType:
            req = APIRequest(
                request_id="req-001", request_type=rt,
                resource_id="res-001",
            )
            resp = service.handle(req)
            self.assertEqual(resp.status, APIResponseStatus.SUCCESS)

    def test_response_all_status_values(self):
        for status in APIResponseStatus:
            resp = APIResponse(
                request_id="req-001", status=status,
                message="ok",
            )
            self.assertEqual(resp.status, status)

    def test_request_no_private_key(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "private_key"))

    def test_response_no_stderr(self):
        resp = APIResponse(
            request_id="req-001", status=APIResponseStatus.SUCCESS,
            message="ok",
        )
        self.assertFalse(hasattr(resp, "stderr"))

    def test_request_no_stdout(self):
        req = APIRequest(
            request_id="req-001", request_type=APIRequestType.BACKUP,
            resource_id="res-001",
        )
        self.assertFalse(hasattr(req, "stdout"))


if __name__ == "__main__":
    unittest.main()
