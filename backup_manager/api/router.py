"""
WorkOps API Router — 路由分发
Sprint014: API Layer Foundation

API 路由入口
Sprint014 只实现 GET 端点
"""

from .response import success_response, list_response
from .errors import NotFoundError, ValidationError


def handle_api_request(method, path, query_params, context):
    """
    API 路由入口
    
    Args:
        method: HTTP 方法 (GET, POST, etc.)
        path: 请求路径
        query_params: 查询参数字典
        context: AppContext 对象
    
    Returns:
        dict: 统一格式响应
    """
    # Sprint014 只支持 GET
    if method != "GET":
        raise ValidationError("Only GET method is allowed in Sprint014")
    
    # Device API
    if path == "/api/v1/devices":
        return handle_get_devices(context)
    
    if path.startswith("/api/v1/devices/"):
        device_id = path[len("/api/v1/devices/"):]
        if device_id:
            return handle_get_device(device_id, context)
    
    # Resource API
    if path == "/api/v1/resources":
        device_id = query_params.get("device_id", "")
        return handle_get_resources(context, device_id)
    
    if path.startswith("/api/v1/resources/"):
        resource_id = path[len("/api/v1/resources/"):]
        if resource_id:
            return handle_get_resource(resource_id, context)
    
    # Operation API
    if path == "/api/v1/operations":
        return handle_get_operations(context)
    
    if path.startswith("/api/v1/operations/"):
        operation_id = path[len("/api/v1/operations/"):]
        if operation_id:
            return handle_get_operation(operation_id, context)
    
    # Task API
    if path == "/api/v1/tasks":
        return handle_get_tasks(context)
    
    if path.startswith("/api/v1/tasks/"):
        task_id = path[len("/api/v1/tasks/"):]
        if task_id:
            return handle_get_task(task_id, context)
    
    # 404
    raise NotFoundError("Endpoint")


def handle_get_devices(context):
    """获取设备列表"""
    devices = context.device_service.list_devices()
    return list_response(devices)


def handle_get_device(device_id, context):
    """获取设备详情"""
    device = context.device_service.get_device(device_id)
    if not device:
        raise NotFoundError("Device")
    return success_response(device)


def handle_get_resources(context, device_id=None):
    """获取资源列表"""
    resources = getattr(context, 'resources', [])
    if device_id:
        resources = [r for r in resources if r.get('device_id') == device_id]
    return list_response(resources)


def handle_get_resource(resource_id, context):
    """获取资源详情"""
    resources = getattr(context, 'resources', [])
    for resource in resources:
        if resource.get('id') == resource_id:
            return success_response(resource)
    raise NotFoundError("Resource")


def handle_get_operations(context):
    """获取操作列表"""
    operations = getattr(context, 'operations', [])
    return list_response(operations)


def handle_get_operation(operation_id, context):
    """获取操作详情"""
    operations = getattr(context, 'operations', [])
    for operation in operations:
        if operation.get('id') == operation_id:
            return success_response(operation)
    raise NotFoundError("Operation")


def handle_get_tasks(context):
    """获取任务列表"""
    tasks = getattr(context, 'tasks', [])
    return list_response(tasks)


def handle_get_task(task_id, context):
    """获取任务详情"""
    tasks = getattr(context, 'tasks', [])
    for task in tasks:
        if task.get('id') == task_id:
            return success_response(task)
    raise NotFoundError("Task")
