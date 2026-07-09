# Sprint015 — Permission Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps Permission Model 基础。

---

# Architecture

```
User
    ↓
Role
    ↓
Permission
    ↓
API Permission Check
```

---

# Goals

- Role Model
- Permission Model
- Permission Checker
- API Integration（基础 middleware）

---

# Role Model

三种角色：

| 角色 | 说明 |
|------|------|
| Admin | 全部权限 |
| Operator | 执行操作 + 查看 |
| Viewer | 只读 |

---

# Permission Model

定义基础 permission key：

| Permission | Admin | Operator | Viewer |
|------------|-------|----------|--------|
| device.read | ✅ | ✅ | ✅ |
| device.manage | ✅ | ❌ | ❌ |
| resource.read | ✅ | ✅ | ✅ |
| resource.manage | ✅ | ❌ | ❌ |
| operation.read | ✅ | ✅ | ✅ |
| operation.execute | ✅ | ✅ | ❌ |
| task.read | ✅ | ✅ | ✅ |
| task.execute | ✅ | ✅ | ❌ |
| history.read | ✅ | ✅ | ✅ |

---

# Permission Checker

负责：

检查当前用户 role 是否拥有 permission。

```python
def check_permission(user_role, permission_key):
    """检查角色是否拥有指定权限"""
    # Admin 拥有所有权限
    if user_role == "admin":
        return True
    
    # 权限映射
    role_permissions = {
        "operator": [
            "device.read", "resource.read",
            "operation.read", "operation.execute",
            "task.read", "task.execute",
            "history.read",
        ],
        "viewer": [
            "device.read", "resource.read",
            "operation.read", "task.read",
            "history.read",
        ],
    }
    
    permissions = role_permissions.get(user_role, [])
    return permission_key in permissions
```

---

# API Integration

只设计基础 middleware。

不修改所有 API。

```python
def require_permission(permission_key):
    """权限检查装饰器"""
    def decorator(func):
        def wrapper(request, *args, **kwargs):
            user = get_current_user(request)
            if not check_permission(user["role"], permission_key):
                raise ForbiddenError()
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

# 禁止

- Database
- JWT
- OAuth
- LDAP
- Task Execution
- Device Execution

---

# 兼容性

保持 M2/M3 已有模块兼容：

- Workspace
- Device Registry
- Resource Registry
- Operation Engine
- Task Engine
- Monitoring Engine
- Scheduler Engine
- History Engine
- API Layer

不得删除。

不得重构。

---

# Output

完成后输出：

1. 修改文件
2. 新增文件
3. 权限测试结果
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。
