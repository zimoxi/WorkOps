"""
WorkOps Unified Operation API — 统一操作 API
Sprint045: Unified Operation API Foundation
"""

from .errors import (
    OperationAPIError,
    InvalidOperationRequestError,
    OperationSubmissionError,
    OperationUnavailableError,
)
from .request import OperationRequestModel
from .response import OperationResponseModel
from .gateway import OperationGateway

# Backward-compatible aliases for legacy server.py
from ._compat import handle_api_request, ApiError, error_response

__all__ = [
    "OperationAPIError",
    "InvalidOperationRequestError",
    "OperationSubmissionError",
    "OperationUnavailableError",
    "OperationRequestModel",
    "OperationResponseModel",
    "OperationGateway",
    # Legacy compat
    "handle_api_request",
    "ApiError",
    "error_response",
]
