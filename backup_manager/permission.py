"""
WorkOps Permission Model — 权限模型
Sprint015: Permission Foundation

复用 Sprint013 AuthService 用户和 Session。
禁止创建新的用户系统。
禁止新增 MOCK_USER_STORE。
"""

# ─── Role Model ──────────────────────────────────────
ROLES = ["admin", "operator", "viewer"]


# ─── Permission Model ────────────────────────────────
# 定义所有 permission key
PERMISSIONS = [
    "device.read",
    "device.manage",
    "resource.read",
    "resource.manage",
    "operation.read",
    "operation.execute",
    "task.read",
    "task.execute",
    "history.read",
]


# ─── Role-Permission Mapping ─────────────────────────
ROLE_PERMISSIONS = {
    "admin": [
        "device.read",
        "device.manage",
        "resource.read",
        "resource.manage",
        "operation.read",
        "operation.execute",
        "task.read",
        "task.execute",
        "history.read",
    ],
    "operator": [
        "device.read",
        "resource.read",
        "operation.read",
        "operation.execute",
        "task.read",
        "task.execute",
        "history.read",
    ],
    "viewer": [
        "device.read",
        "resource.read",
        "operation.read",
        "task.read",
        "history.read",
    ],
}


# ─── Permission Checker ──────────────────────────────
def check_permission(user_role, permission_key):
    """
    检查角色是否拥有指定权限。
    
    Args:
        user_role: 用户角色 (admin, operator, viewer)
        permission_key: 权限键 (如 device.read)
    
    Returns:
        bool: 是否拥有权限
    """
    if user_role not in ROLES:
        return False
    
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    return permission_key in permissions


def require_permission(permission_key):
    """
    权限检查装饰器/函数。
    
    Args:
        permission_key: 需要检查的权限键
    
    Returns:
        函数：接受 user_role 参数，返回是否有权限
    """
    def checker(user_role):
        return check_permission(user_role, permission_key)
    return checker


def get_user_permissions(user_role):
    """
    获取角色的所有权限。
    
    Args:
        user_role: 用户角色
    
    Returns:
        list: 权限列表
    """
    return ROLE_PERMISSIONS.get(user_role, [])
