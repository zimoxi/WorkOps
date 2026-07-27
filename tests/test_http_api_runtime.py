"""
WorkOps HTTP API Runtime Tests
Sprint066: HTTP API Runtime Foundation

覆盖：
- HTTPRequest validation
- HTTPResponse validation
- HTTPApplication contract
- APIRouter contract
- Endpoint contracts (Health, Backup, Restore, Status)
- SecurityMiddleware contract
- Error model
- Security boundary
"""

import unittest
from datetime import datetime, timezone

from backup_manager.http_api.models import HTTPRequest, HTTPResponse
from backup_manager.http_api.app import HTTPApplication
from backup_manager.http_api.router import APIRouter
from backup_manager.http_api.endpoints import (
    HealthEndpoint,
    BackupEndpoint,
    RestoreEndpoint,
    StatusEndpoint,
)
from backup_manager.http_api.middleware import SecurityMiddleware
from backup_manager.http_api.errors import (
    HTTPAPIError,
    InvalidHTTPRequestError,
    HTTPRouteError,
    HTTPServiceUnavailableError,
)


# ============================================================================
# HTTPRequest
# ============================================================================

class TestHTTPRequest(unittest.TestCase):
    """HTTP 请求测试"""

    def _make_request(self, **kwargs):
        defaults = {
            "request_id": "req-001",
            "endpoint": "/health",
        }
        defaults.update(kwargs)
        return HTTPRequest(**defaults)

    def test_valid_request(self):
        req = self._make_request()
        self.assertEqual(req.request_id, "req-001")
        self.assertEqual(req.endpoint, "/health")

    def test_frozen(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.request_id = "other"

    def test_slots(self):
        req = self._make_request()
        with self.assertRaises(AttributeError):
            req.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_request(request_id="")

    def test_empty_endpoint_rejected(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_request(endpoint="")

    def test_timezone_aware(self):
        req = self._make_request()
        self.assertIsNotNone(req.created_at.tzinfo)

    def test_all_endpoints(self):
        for ep in ["/health", "/status", "/backup", "/restore"]:
            req = self._make_request(endpoint=ep)
            self.assertEqual(req.endpoint, ep)

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
# HTTPResponse
# ============================================================================

class TestHTTPResponse(unittest.TestCase):
    """HTTP 响应测试"""

    def _make_response(self, **kwargs):
        defaults = {
            "request_id": "req-001",
            "status_code": 200,
            "message": "ok",
        }
        defaults.update(kwargs)
        return HTTPResponse(**defaults)

    def test_valid_response(self):
        resp = self._make_response()
        self.assertEqual(resp.request_id, "req-001")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.message, "ok")

    def test_frozen(self):
        resp = self._make_response()
        with self.assertRaises(AttributeError):
            resp.request_id = "other"

    def test_slots(self):
        resp = self._make_response()
        with self.assertRaises(AttributeError):
            resp.__dict__

    def test_empty_request_id_rejected(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_response(request_id="")

    def test_invalid_status_code_low(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_response(status_code=99)

    def test_invalid_status_code_high(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_response(status_code=600)

    def test_invalid_status_code_type(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_response(status_code="200")

    def test_message_must_be_str(self):
        with self.assertRaises(InvalidHTTPRequestError):
            self._make_response(message=123)

    def test_timezone_aware(self):
        resp = self._make_response()
        self.assertIsNotNone(resp.created_at.tzinfo)

    def test_all_status_codes(self):
        for code in [200, 201, 204, 400, 401, 403, 404, 500, 502, 503]:
            resp = self._make_response(status_code=code)
            self.assertEqual(resp.status_code, code)

    def test_no_forbidden_fields(self):
        resp = self._make_response()
        for attr in ["password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(resp, attr))

    def test_repr_no_secrets(self):
        resp = self._make_response()
        r = repr(resp)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())


# ============================================================================
# HTTPApplication Contract
# ============================================================================

class TestHTTPApplicationContract(unittest.TestCase):
    """HTTP 应用契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(HTTPApplication, ABC))

    def test_has_create_app(self):
        self.assertTrue(hasattr(HTTPApplication, "create_app"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            HTTPApplication()

    def test_concrete_subclass(self):
        class MockApp(HTTPApplication):
            def create_app(self):
                return {"status": "created"}
        app = MockApp()
        result = app.create_app()
        self.assertEqual(result["status"], "created")

    def test_missing_create_app(self):
        class BadApp(HTTPApplication):
            pass
        with self.assertRaises(TypeError):
            BadApp()


# ============================================================================
# APIRouter Contract
# ============================================================================

class TestAPIRouterContract(unittest.TestCase):
    """API 路由契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(APIRouter, ABC))

    def test_has_register_routes(self):
        self.assertTrue(hasattr(APIRouter, "register_routes"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            APIRouter()

    def test_concrete_subclass(self):
        class MockRouter(APIRouter):
            def __init__(self):
                self.routes = []
            def register_routes(self):
                self.routes = ["/health", "/status", "/backup", "/restore"]
        router = MockRouter()
        router.register_routes()
        self.assertEqual(len(router.routes), 4)

    def test_missing_register_routes(self):
        class BadRouter(APIRouter):
            pass
        with self.assertRaises(TypeError):
            BadRouter()


# ============================================================================
# Endpoint Contracts
# ============================================================================

class TestHealthEndpointContract(unittest.TestCase):
    """健康检查端点契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(HealthEndpoint, ABC))

    def test_has_handle(self):
        self.assertTrue(hasattr(HealthEndpoint, "handle"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            HealthEndpoint()

    def test_concrete_subclass(self):
        class MockEndpoint(HealthEndpoint):
            def handle(self, request):
                return HTTPResponse(
                    request_id=request.request_id,
                    status_code=200, message="healthy",
                )
        ep = MockEndpoint()
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        resp = ep.handle(req)
        self.assertEqual(resp.status_code, 200)


class TestBackupEndpointContract(unittest.TestCase):
    """备份端点契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(BackupEndpoint, ABC))

    def test_has_handle(self):
        self.assertTrue(hasattr(BackupEndpoint, "handle"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            BackupEndpoint()

    def test_concrete_subclass(self):
        class MockEndpoint(BackupEndpoint):
            def handle(self, request):
                return HTTPResponse(
                    request_id=request.request_id,
                    status_code=200, message="backup started",
                )
        ep = MockEndpoint()
        req = HTTPRequest(request_id="req-001", endpoint="/backup")
        resp = ep.handle(req)
        self.assertEqual(resp.status_code, 200)


class TestRestoreEndpointContract(unittest.TestCase):
    """恢复端点契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(RestoreEndpoint, ABC))

    def test_has_handle(self):
        self.assertTrue(hasattr(RestoreEndpoint, "handle"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            RestoreEndpoint()

    def test_concrete_subclass(self):
        class MockEndpoint(RestoreEndpoint):
            def handle(self, request):
                return HTTPResponse(
                    request_id=request.request_id,
                    status_code=200, message="restore started",
                )
        ep = MockEndpoint()
        req = HTTPRequest(request_id="req-001", endpoint="/restore")
        resp = ep.handle(req)
        self.assertEqual(resp.status_code, 200)


class TestStatusEndpointContract(unittest.TestCase):
    """状态端点契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(StatusEndpoint, ABC))

    def test_has_handle(self):
        self.assertTrue(hasattr(StatusEndpoint, "handle"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            StatusEndpoint()

    def test_concrete_subclass(self):
        class MockEndpoint(StatusEndpoint):
            def handle(self, request):
                return HTTPResponse(
                    request_id=request.request_id,
                    status_code=200, message="running",
                )
        ep = MockEndpoint()
        req = HTTPRequest(request_id="req-001", endpoint="/status")
        resp = ep.handle(req)
        self.assertEqual(resp.status_code, 200)


# ============================================================================
# SecurityMiddleware Contract
# ============================================================================

class TestSecurityMiddlewareContract(unittest.TestCase):
    """安全中间件契约测试"""

    def test_is_abc(self):
        from abc import ABC
        self.assertTrue(issubclass(SecurityMiddleware, ABC))

    def test_has_process(self):
        self.assertTrue(hasattr(SecurityMiddleware, "process"))

    def test_cannot_instantiate(self):
        with self.assertRaises(TypeError):
            SecurityMiddleware()

    def test_concrete_subclass(self):
        class MockMiddleware(SecurityMiddleware):
            def process(self, request):
                return request
        mw = MockMiddleware()
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        result = mw.process(req)
        self.assertEqual(result.request_id, "req-001")

    def test_missing_process(self):
        class BadMiddleware(SecurityMiddleware):
            pass
        with self.assertRaises(TypeError):
            BadMiddleware()


# ============================================================================
# Error Model
# ============================================================================

class TestHTTPErrors(unittest.TestCase):
    """错误模型测试"""

    def test_http_api_error(self):
        with self.assertRaises(HTTPAPIError):
            raise HTTPAPIError("test")

    def test_invalid_request_error(self):
        with self.assertRaises(HTTPAPIError):
            raise InvalidHTTPRequestError("test")

    def test_route_error(self):
        with self.assertRaises(HTTPAPIError):
            raise HTTPRouteError("test")

    def test_unavailable_error(self):
        with self.assertRaises(HTTPAPIError):
            raise HTTPServiceUnavailableError("test")

    def test_error_messages_no_secrets(self):
        for exc_cls, args in [
            (HTTPAPIError, ("test",)),
            (InvalidHTTPRequestError, ("test",)),
            (HTTPRouteError, ("test",)),
            (HTTPServiceUnavailableError, ("test",)),
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
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        for attr in ["password", "credential", "secret", "token", "command", "ssh"]:
            self.assertFalse(hasattr(req, attr))

    def test_response_no_credentials(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        for attr in ["password", "secret", "credential", "token", "command"]:
            self.assertFalse(hasattr(resp, attr))

    def test_no_subprocess(self):
        import ast
        import os
        http_dir = os.path.join("backup_manager", "http_api")
        for filename in os.listdir(http_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(http_dir, filename)
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
        http_dir = os.path.join("backup_manager", "http_api")
        for filename in os.listdir(http_dir):
            if not filename.endswith(".py"):
                continue
            filepath = os.path.join(http_dir, filename)
            with open(filepath) as f:
                tree = ast.parse(f.read())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Name) and func.id in ("exec", "eval"):
                        self.fail(f"{func.id}() in {filename}")

    def test_endpoint_lifecycle(self):
        """完整端点生命周期"""
        class MockEndpoint(HealthEndpoint):
            def handle(self, request):
                return HTTPResponse(
                    request_id=request.request_id,
                    status_code=200, message="healthy",
                )
        ep = MockEndpoint()
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        resp = ep.handle(req)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.message, "healthy")


# ============================================================================
# Extended Tests
# ============================================================================

class TestHTTPAPIExtended(unittest.TestCase):
    """扩展测试"""

    def test_error_hierarchy(self):
        self.assertTrue(issubclass(InvalidHTTPRequestError, HTTPAPIError))
        self.assertTrue(issubclass(HTTPRouteError, HTTPAPIError))
        self.assertTrue(issubclass(HTTPServiceUnavailableError, HTTPAPIError))

    def test_request_repr_no_secrets(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        r = repr(req)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_response_repr_no_secrets(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        r = repr(resp)
        for term in ["password", "secret", "token"]:
            self.assertNotIn(term, r.lower())

    def test_request_preserves_all_fields(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertEqual(req.request_id, "req-001")
        self.assertEqual(req.endpoint, "/health")

    def test_response_preserves_all_fields(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertEqual(resp.request_id, "req-001")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.message, "ok")

    def test_request_whitespace_id_rejected(self):
        with self.assertRaises(InvalidHTTPRequestError):
            HTTPRequest(request_id="   ", endpoint="/health")

    def test_request_whitespace_endpoint_rejected(self):
        with self.assertRaises(InvalidHTTPRequestError):
            HTTPRequest(request_id="req-001", endpoint="   ")

    def test_response_empty_message_accepted(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="")
        self.assertEqual(resp.message, "")

    def test_request_no_password(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "password"))

    def test_request_no_secret(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "secret"))

    def test_request_no_token(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "token"))

    def test_request_no_command(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "command"))

    def test_response_no_password(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "password"))

    def test_response_no_secret(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "secret"))

    def test_response_no_token(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "token"))

    def test_error_messages_safe(self):
        try:
            raise HTTPAPIError("test")
        except HTTPAPIError as e:
            msg = str(e)
            for term in ["password", "secret", "token", "command"]:
                self.assertNotIn(term, msg.lower())

    def test_route_error_message(self):
        exc = HTTPRouteError("route not found")
        self.assertIn("route not found", str(exc))

    def test_unavailable_error_message(self):
        exc = HTTPServiceUnavailableError("service down")
        self.assertIn("service down", str(exc))

    def test_all_endpoints_handle(self):
        """所有端点都能处理请求"""
        endpoints = [
            (HealthEndpoint, "/health", "healthy"),
            (BackupEndpoint, "/backup", "backup started"),
            (RestoreEndpoint, "/restore", "restore started"),
            (StatusEndpoint, "/status", "running"),
        ]
        for EndpointClass, path, msg in endpoints:
            class MockEp(EndpointClass):
                def handle(self, request):
                    return HTTPResponse(
                        request_id=request.request_id,
                        status_code=200, message=msg,
                    )
            ep = MockEp()
            req = HTTPRequest(request_id="req-001", endpoint=path)
            resp = ep.handle(req)
            self.assertEqual(resp.status_code, 200)

    def test_response_all_error_codes(self):
        for code in [400, 401, 403, 404, 500, 502, 503]:
            resp = HTTPResponse(request_id="req-001", status_code=code, message="error")
            self.assertEqual(resp.status_code, code)

    def test_request_no_credential(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "credential"))

    def test_response_no_credential(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "credential"))

    def test_middleware_returns_request(self):
        class MockMiddleware(SecurityMiddleware):
            def process(self, request):
                return request
        mw = MockMiddleware()
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        result = mw.process(req)
        self.assertIsInstance(result, HTTPRequest)

    def test_router_register_returns_none(self):
        class MockRouter(APIRouter):
            def register_routes(self):
                pass
        router = MockRouter()
        result = router.register_routes()
        self.assertIsNone(result)

    def test_request_all_fields_present(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertTrue(hasattr(req, "request_id"))
        self.assertTrue(hasattr(req, "endpoint"))
        self.assertTrue(hasattr(req, "created_at"))

    def test_response_all_fields_present(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertTrue(hasattr(resp, "request_id"))
        self.assertTrue(hasattr(resp, "status_code"))
        self.assertTrue(hasattr(resp, "message"))
        self.assertTrue(hasattr(resp, "created_at"))

    def test_request_no_ssh(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "ssh"))

    def test_request_no_stdout(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "stdout"))

    def test_response_no_stderr(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "stderr"))

    def test_response_no_command(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "command"))

    def test_response_no_stdout(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "stdout"))

    def test_middleware_passes_through(self):
        class MockMiddleware(SecurityMiddleware):
            def process(self, request):
                return request
        mw = MockMiddleware()
        for ep in ["/health", "/status", "/backup", "/restore"]:
            req = HTTPRequest(request_id="req-001", endpoint=ep)
            result = mw.process(req)
            self.assertEqual(result.endpoint, ep)

    def test_endpoint_failed_response(self):
        class MockEndpoint(HealthEndpoint):
            def handle(self, request):
                return HTTPResponse(
                    request_id=request.request_id,
                    status_code=500, message="error",
                )
        ep = MockEndpoint()
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        resp = ep.handle(req)
        self.assertEqual(resp.status_code, 500)

    def test_request_no_private_key(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "private_key"))

    def test_response_no_private_key(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "private_key"))

    def test_request_no_credential_value(self):
        req = HTTPRequest(request_id="req-001", endpoint="/health")
        self.assertFalse(hasattr(req, "credential_value"))

    def test_response_no_credential_value(self):
        resp = HTTPResponse(request_id="req-001", status_code=200, message="ok")
        self.assertFalse(hasattr(resp, "credential_value"))

    def test_app_returns_object(self):
        class MockApp(HTTPApplication):
            def create_app(self):
                return {"type": "http", "status": "ready"}
        app = MockApp()
        result = app.create_app()
        self.assertIsInstance(result, dict)


if __name__ == "__main__":
    unittest.main()
