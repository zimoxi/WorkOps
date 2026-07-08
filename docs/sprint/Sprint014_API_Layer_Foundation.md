# Sprint014 - API Layer Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps API Layer 基础。

---

# Goals

- API Response 统一格式
- API Error Handling
- API Router 基础结构
- Service 调用边界

---

# Scope

允许：

- REST API
- JSON Response
- Error Code
- Request Validation

禁止：

- Database
- ORM
- JWT
- OAuth
- Permission Enforcement
- Device Execution
- Task Execution

---

# Architecture

```
Frontend
    ↓
API Layer
    ↓
Service Layer
    ↓
Existing Mock/Service
```

---

# API Response Format

统一响应格式：

```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": null
}
```

错误响应：

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device not found"
  },
  "meta": null
}
```

---

# Error Codes

| Code | HTTP Status | 说明 |
|------|-------------|------|
| VALIDATION_ERROR | 400 | 请求参数错误 |
| UNAUTHORIZED | 401 | 未认证 |
| FORBIDDEN | 403 | 无权限 |
| NOT_FOUND | 404 | 资源不存在 |
| CONFLICT | 409 | 资源冲突 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |

---

# API Endpoints

## Device API

```
GET    /api/devices           → 设备列表
GET    /api/devices/:id       → 设备详情
POST   /api/devices           → 创建设备
PUT    /api/devices/:id       → 更新设备
DELETE /api/devices/:id       → 删除设备
```

## Resource API

```
GET    /api/resources         → 资源列表
GET    /api/resources/:id     → 资源详情
GET    /api/resources?device_id=xxx → 按设备筛选
```

## Operation API

```
GET    /api/operations        → 操作列表
GET    /api/operations/:id    → 操作详情
POST   /api/operations        → 创建操作
PUT    /api/operations/:id    → 更新操作
DELETE /api/operations/:id    → 删除操作
```

## Task API

```
GET    /api/tasks             → 任务列表
GET    /api/tasks/:id         → 任务详情
POST   /api/tasks             → 创建任务
```

---

# Request Validation

验证规则：

- 必填字段检查
- 类型检查
- 长度限制
- 格式验证

验证失败返回：

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "name", "message": "Name is required" }
    ]
  }
}
```

---

# Service Layer Boundary

API Layer 只负责：

- 接收 HTTP 请求
- 验证请求参数
- 调用 Service Layer
- 返回统一格式响应

API Layer 不负责：

- 业务逻辑
- 数据访问
- 设备连接
- 命令执行

---

# Module Constraints

API Layer 是新增模块。

不修改现有 Service。

不修改现有 Mock。

不修改现有 Store。

---

# Existing Modules

必须保持兼容：

- Workspace
- Device Registry
- Resource Registry
- Operation Engine
- Task Engine
- Monitoring Engine
- Scheduler Engine
- History Engine

不得删除。

不得重构。

不得修改业务逻辑。

---

# Output

完成后输出：

1. 修改文件
2. 新增文件
3. API 测试结果
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。
