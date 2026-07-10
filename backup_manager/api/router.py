"""
WorkOps API Router — 路由分发
Sprint014: API Layer Foundation
Sprint015: Permission Foundation
Sprint016: Repository Layer Foundation

API 路由入口
集成权限检查
调用 Service Layer
"""

from .response import success_response, list_response
from .errors import NotFoundError, ValidationError, ForbiddenError
from ..permission import check_permission


def handle_api_request(method, path, query_params, context, user=None):
    """
    API 路由入口
    
    Args:
        method: HTTP 方法 (GET, POST, etc.)
        path: 请求路径
        query_params: 查询参数字典
        context: AppContext 对象
        user: 当前用户信息 (Sprint015)
    
    Returns:
        dict: 统一格式响应
    """
    # Sprint014 只支持 GET
    if method != "GET":
        raise ValidationError("Only GET method is allowed in Sprint014")
    
    # 获取用户角色
    user_role = user.get("role", "viewer") if user else "viewer"
    
    # Device API
    if path == "/api/v1/devices":
        check_permission_or_raise(user_role, "device.read")
        return handle_get_devices(context)
    
    if path.startswith("/api/v1/devices/"):
        device_id = path[len("/api/v1/devices/"):]
        if device_id:
            check_permission_or_raise(user_role, "device.read")
            return handle_get_device(device_id, context)
    
    # Resource API
    if path == "/api/v1/resources":
        check_permission_or_raise(user_role, "resource.read")
        device_id = query_params.get("device_id", "")
        return handle_get_resources(context, device_id)
    
    if path.startswith("/api/v1/resources/"):
        resource_id = path[len("/api/v1/resources/"):]
        if resource_id:
            check_permission_or_raise(user_role, "resource.read")
            return handle_get_resource(resource_id, context)
    
    # Operation API
    if path == "/api/v1/operations":
        check_permission_or_raise(user_role, "operation.read")
        return handle_get_operations(context)
    
    if path.startswith("/api/v1/operations/"):
        operation_id = path[len("/api/v1/operations/"):]
        if operation_id:
            check_permission_or_raise(user_role, "operation.read")
            return handle_get_operation(operation_id, context)
    
    # Task API
    if path == "/api/v1/tasks":
        check_permission_or_raise(user_role, "task.read")
        return handle_get_tasks(context)
    
    if path.startswith("/api/v1/tasks/"):
        task_id = path[len("/api/v1/tasks/"):]
        if task_id:
            check_permission_or_raise(user_role, "task.read")
            return handle_get_task(task_id, context)
    
    # 404
    raise NotFoundError("Endpoint")


def check_permission_or_raise(user_role, permission_key):
    """
    检查权限，如果没有权限则抛出 ForbiddenError
    
    Args:
        user_role: 用户角色
        permission_key: 权限键
    """
    if not check_permission(user_role, permission_key):
        raise ForbiddenError(f"Permission denied: {permission_key}")


def handle_get_devices(context):
    """获取设备列表 — 调用 Service"""
    devices = context.api_device_service.get_all_devices()
    return list_response(devices)


def handle_get_device(device_id, context):
    """获取设备详情 — 调用 Service"""
    device = context.api_device_service.get_device_by_id(device_id)
    if not device:
        raise NotFoundError("Device")
    return success_response(device)


def handle_get_resources(context, device_id=None):
    """获取资源列表 — 调用 Service"""
    resources = context.api_resource_service.get_all_resources()
    if device_id:
        resources = [r for r in resources if r.get('device_id') == device_id]
    return list_response(resources)


def handle_get_resource(resource_id, context):
    """获取资源详情 — 调用 Service"""
    resource = context.api_resource_service.get_resource_by_id(resource_id)
    if not resource:
        raise NotFoundError("Resource")
    return success_response(resource)


def handle_get_operations(context):
    """获取操作列表 — 调用 Service"""
    operations = context.api_operation_service.get_all_operations()
    return list_response(operations)


def handle_get_operation(operation_id, context):
    """获取操作详情 — 调用 Service"""
    operation = context.api_operation_service.get_operation_by_id(operation_id)
    if not operation:
        raise NotFoundError("Operation")
    return success_response(operation)


def handle_get_tasks(context):
    """获取任务列表 — 调用 Service"""
    tasks = context.api_task_service.get_all_tasks()
    return list_response(tasks)


def handle_get_task(task_id, context):
    """获取任务详情 — 调用 Service"""
    task = context.api_task_service.get_task_by_id(task_id)
    if not task:
        raise NotFoundError("Task")
    return success_response(task)
