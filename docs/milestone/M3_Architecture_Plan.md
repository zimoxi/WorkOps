# M3 Real Capability Architecture Plan

Version: 1.1

Date: 2026-07-04

Status: Ready for Review

---

# 1. M3 总体目标

将 WorkOps 从 Mock First 平台逐步连接真实能力。

M3 不修改 M2 架构，只在其上层添加真实能力层。

```
┌─────────────────────────────────────────────────┐
│                   M3 Layer                       │
│  Authentication → API → Service → Repository     │
│  Executor → Device Adapter → Discovery → Audit   │
├─────────────────────────────────────────────────┤
│                   M2 Layer（保留）                │
│  Device → Resource → Operation → Task            │
│  Scheduler → History → Monitoring                │
│  Unified Store → Components                      │
└─────────────────────────────────────────────────┘
```

---

# 2. M2 → M3 架构变化

## 2.1 M2 现状

```
Frontend (app.js)
    ↓ 直接调用
Modules (device-registry.js, resource-registry.js, ...)
    ↓ 直接读取
Unified Store (stores/index.js)
```

## 2.2 M3 目标

```
Frontend (app.js)
    ↓ HTTP API
API Layer (server.py)
    ↓ 认证 + 权限检查
Service Layer (Python)
    ↓ 业务逻辑
Repository Layer (Python)
    ↓ 数据访问抽象
Mock Repository / Database Repository
    ↓
Mock Data / 真实数据库
```

## 2.3 关键变化

| 层 | M2 | M3 |
|----|----|----|
| Frontend | 直接读 Store | 调用 API |
| 数据来源 | Mock Store | API → Service → Repository |
| 认证 | 无 | Session + Cookie |
| 执行 | 无 | Executor 框架（Task 唯一入口） |
| 设备连接 | 无 | DeviceAdapter 抽象接口 |
| 审计 | 无 | Audit Log |

## 2.4 Repository Layer（新增）

M2 Store 保留用于 Mock/Test。

M3 新增 Repository Layer，提供数据访问抽象：

```
Frontend
    ↓
API
    ↓
Service
    ↓
Repository Interface
    ↓
┌────────────────────┬────────────────────┐
│ Mock Repository    │ Database Repository│
│ (M2 Store 封装)    │ (真实数据库)        │
└────────────────────┴────────────────────┘
```

Repository Interface 不绑定具体数据库实现。

---

# 3. Authentication Architecture

## 3.1 第一阶段：Session + Cookie

```
┌─────────────────────────────────────────────────┐
│              Authentication Layer                │
├─────────────────────────────────────────────────┤
│  Login Page                                      │
│    ↓                                             │
│  POST /api/auth/login                            │
│    ↓                                             │
│  AuthService.validate(username, password)        │
│    ↓                                             │
│  Session 创建 + Cookie 设置                       │
│    ↓                                             │
│  后续请求携带 Session Cookie                      │
└─────────────────────────────────────────────────┘
```

注意：JWT 放未来 External API 阶段。

## 3.2 用户模型

```python
class User:
    id: str           # UUID
    username: str     # 用户名
    password_hash: str # 密码哈希
    role: str         # admin / operator / viewer
    created_at: str   # 创建时间
    last_login: str   # 最后登录
```

## 3.3 角色权限

| 角色 | 设备管理 | 操作执行 | 查看历史 | 系统设置 |
|------|----------|----------|----------|----------|
| Admin | ✅ | ✅ | ✅ | ✅ |
| Operator | ❌ | ✅ | ✅ | ❌ |
| Viewer | ❌ | ❌ | ✅ | ❌ |

## 3.4 API 端点

```
POST /api/auth/login      → 登录（创建 Session）
POST /api/auth/logout     → 登出（销毁 Session）
GET  /api/auth/me         → 获取当前用户
```

---

# 4. Permission Model

## 4.1 权限检查流程

```
API Request
    ↓
SessionMiddleware.verify_session()
    ↓
PermissionMiddleware.check_role(required_role)
    ↓
Service.execute()
```

## 4.2 权限装饰器

```python
@require_role("admin")
def create_device():
    ...

@require_role("operator")
def execute_operation():
    ...

@require_role("viewer")
def get_history():
    ...
```

---

# 5. API Layer Architecture

## 5.1 API 结构

```
/api/
├── auth/           → 认证相关
├── devices/        → 设备 CRUD
├── resources/      → 资源 CRUD
├── operations/     → 操作 CRUD
├── tasks/          → 任务 CRUD
├── schedules/      → 调度 CRUD
├── history/        → 历史查询
├── monitoring/     → 监控数据
└── system/         → 系统信息
```

## 5.2 统一响应格式

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "page": 1,
    "total": 100
  }
}
```

---

# 6. Service Layer Architecture

## 6.1 Service 结构

```
backup_manager/
├── services/
│   ├── __init__.py
│   ├── auth_service.py       → 认证服务
│   ├── device_service.py     → 设备服务
│   ├── resource_service.py   → 资源服务
│   ├── operation_service.py  → 操作服务
│   ├── task_service.py       → 任务服务
│   ├── schedule_service.py   → 调度服务
│   ├── history_service.py    → 历史服务
│   ├── monitoring_service.py → 监控服务
│   └── audit_service.py      → 审计服务
```

## 6.2 Service 与 Repository 的关系

```
Service
    ↓ 调用
Repository Interface
    ↓ 注入
Mock Repository 或 Database Repository
```

Service 不直接访问数据库，通过 Repository 接口解耦。

---

# 7. Repository Layer Architecture

## 7.1 Repository Interface

```python
class DeviceRepository(ABC):
    @abstractmethod
    def list_all(self, filters=None) -> List[Device]
    
    @abstractmethod
    def get_by_id(self, device_id: str) -> Device
    
    @abstractmethod
    def create(self, data: dict) -> Device
    
    @abstractmethod
    def update(self, device_id: str, data: dict) -> Device
    
    @abstractmethod
    def delete(self, device_id: str) -> bool
```

## 7.2 Mock Repository（M2 Store 封装）

```python
class MockDeviceRepository(DeviceRepository):
    def __init__(self):
        self.data = MOCK_DEVICE_STORE
    
    def list_all(self, filters=None):
        return self.data
```

## 7.3 Database Repository（真实数据库）

```python
class DatabaseDeviceRepository(DeviceRepository):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def list_all(self, filters=None):
        return self.db.query(Device).filter(filters).all()
```

## 7.4 数据库不提前绑定

使用 Repository Interface，具体实现可替换：

- Mock Repository：开发/测试阶段
- Database Repository：生产阶段
- 未来可扩展：PostgreSQL / SQLite / 其他

---

# 8. Execution Layer Architecture

## 8.1 Task 是唯一执行入口

```
Task.create(operation_id, device_id)
    ↓
ExecutorFactory.get_executor(operation_type)
    ↓
Executor.validate(task)
    ↓
Executor.execute(task)
    ↓
DeviceAdapter.connect(device)
    ↓
DeviceAdapter.execute(command)
    ↓
ResultCollector.collect(output)
    ↓
Task.update_status(result)
    ↓
History.record(task, result)
```

**禁止：Operation 直接调用 Adapter。**

Task 是唯一执行入口，Operation 只定义"做什么"。

## 8.2 Executor 接口

```python
class BaseExecutor(ABC):
    @abstractmethod
    def validate(self, task: Task) -> bool
    
    @abstractmethod
    def execute(self, task: Task) -> ExecutionResult
    
    @abstractmethod
    def cancel(self, task_id: str) -> bool
```

---

# 9. Device Adapter Architecture

## 9.1 DeviceAdapter 抽象接口

```python
class DeviceAdapter(ABC):
    @abstractmethod
    def connect(self, device: Device) -> bool
    
    @abstractmethod
    def disconnect(self) -> None
    
    @abstractmethod
    def execute(self, command: str) -> CommandResult
    
    @abstractmethod
    def queryStatus(self) -> DeviceStatus
```

## 9.2 具体适配器

| 适配器 | 目标设备 | 协议 |
|--------|----------|------|
| SSHAdapter | Linux / NAS / OMV | SSH (paramiko) |
| WinRMAdapter | Windows | WinRM |
| SNMPAdapter | 网络设备 / UPS | SNMP |

## 9.3 适配器注册

```python
class DeviceAdapterRegistry:
    _adapters = {}
    
    @classmethod
    def register(cls, device_type: str, adapter_class):
        cls._adapters[device_type] = adapter_class
    
    @classmethod
    def get_adapter(cls, device_type: str) -> DeviceAdapter:
        return cls._adapters.get(device_type)

# 注册
DeviceAdapterRegistry.register("linux", SSHAdapter)
DeviceAdapterRegistry.register("nas", SSHAdapter)
DeviceAdapterRegistry.register("windows", WinRMAdapter)
```

---

# 10. Mock 与真实数据切换策略

## 10.1 切换机制

```python
# config.yaml
data_source:
  mode: "mock"  # mock / real
```

## 10.2 切换流程

```
M2 阶段（当前）：
  Frontend → Store.getAll() → Mock 数据

M3 阶段（过渡）：
  Frontend → API → Service → MockRepository → Mock 数据

M3 阶段（完成）：
  Frontend → API → Service → DatabaseRepository → 真实数据库
```

## 10.3 渐进迁移

| 阶段 | 数据来源 | 说明 |
|------|----------|------|
| Sprint013-014 | Mock Store | 前端仍用 Mock |
| Sprint015 | API + MockRepository | 前端调用 API，API 通过 MockRepository 返回 |
| Sprint016 | API + DatabaseRepository | 前端调用 API，API 读写数据库 |
| Sprint017+ | 真实数据 | 设备连接 + 资源发现 |

---

# 11. Backward Compatibility Strategy

## 11.1 兼容原则

- M2 所有功能必须继续工作
- M2 Store 保留用于 Mock/Test
- 旧模块不受影响
- 导航结构保持不变
- i18n 保持不变

## 11.2 M2 Store 保留

M2 Store 不修改，不增加 API 能力：

```js
// M2 Store 保持原样
window.DeviceStore = {
  getAll: function () { return data.slice(); },
  getById: function (id) { ... }
};
```

M3 通过 Repository Layer 封装 M2 Store，供 MockRepository 使用。

---

# 12. Migration Plan

## 12.1 数据库迁移

```
Sprint013: 创建 users 表
Sprint014: 创建 api_sessions 表
Sprint016: 创建 audit_logs 表
```

## 12.2 代码迁移

```
Sprint013: 新增 auth 模块
Sprint014: 新增 API 层 + Repository Interface
Sprint015: 新增 Executor 框架
Sprint016: 新增 DeviceAdapter 接口 + SSHAdapter
Sprint017: 新增 Resource Discovery
Sprint018: 新增 Audit 模块
```

---

# 13. Sprint 划分建议

| Sprint | 名称 | 目标 | 依赖 |
|--------|------|------|------|
| Sprint013 | Authentication Foundation | Session + Cookie 认证、角色权限 | 无 |
| Sprint014 | API Layer Foundation | RESTful API、Repository Interface、MockRepository | Sprint013 |
| Sprint015 | Execution Layer Foundation | Task → Executor 框架（Task 唯一入口） | Sprint014 |
| Sprint016 | Device Adapter Foundation | DeviceAdapter 接口、SSHAdapter 实现 | Sprint014 |
| Sprint017 | Resource Discovery Foundation | 真实资源发现 | Sprint016 |
| Sprint018 | Audit & Security Foundation | 审计日志、安全策略 | Sprint013 |

---

# Output

1. M3 总体目标 ✅
2. M2 → M3 架构变化 ✅
3. Authentication Architecture ✅（Session + Cookie）
4. Permission Model ✅
5. API Layer Architecture ✅
6. Service Layer Architecture ✅
7. Repository Layer Architecture ✅（新增）
8. Execution Layer Architecture ✅（Task 唯一入口）
9. Device Adapter Architecture ✅（抽象接口）
10. Mock 与真实数据切换策略 ✅
11. Backward Compatibility Strategy ✅（M2 Store 不修改）
12. Migration Plan ✅
13. Sprint 划分建议 ✅

---

**等待 Review。**
