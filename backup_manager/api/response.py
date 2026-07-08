"""
WorkOps API Response — 统一响应格式
Sprint014: API Layer Foundation

统一成功/错误响应格式
"""


def success_response(data):
    """统一成功响应"""
    return {
        "success": True,
        "data": data,
        "error": None,
    }


def error_response(code, message, details=None):
    """统一错误响应"""
    error = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details
    return {
        "success": False,
        "data": None,
        "error": error,
    }


def list_response(items, total=None):
    """列表响应"""
    return success_response({
        "items": items,
        "total": total if total is not None else len(items),
    })
