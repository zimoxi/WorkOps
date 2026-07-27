"""
Backward-compatible aliases for legacy server.py (pre-Sprint045 API).

server.py imports handle_api_request, ApiError, error_response from .api.
Sprint045 replaced the old module with new domain models.
This file provides shim functions so server.py can still import.
"""


class ApiError(Exception):
    """Legacy API error used by server.py."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def error_response(code: str, message: str) -> dict:
    """Legacy error response builder used by server.py."""
    return {"error": {"code": code, "message": message}}


def handle_api_request(
    method: str,
    path: str,
    params: dict,
    context,
    user=None,
) -> dict:
    """
    Legacy API request handler used by server.py.
    This is a stub — the real implementation is in the HTTP API layer.
    """
    raise ApiError("NOT_IMPLEMENTED", f"API endpoint not implemented: {method} {path}", 501)
