# Sprint016 — Repository Layer Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 Repository Layer，解除 API 与 Mock 数据耦合。

---

# Architecture

```
Frontend
    ↓
API Layer
    ↓
Service Layer
    ↓
Repository Layer
    ↓
MockRepository
```

---

# Goals

- Repository Interface
- MockRepository 实现
- Service Layer 新增
- API Migration

---

# Repository Interface

定义统一接口：

| Repository | 方法 |
|------------|------|
| DeviceRepository | `get_all()`, `get_by_id(id)` |
| ResourceRepository | `get_all()`, `get_by_id(id)` |
| OperationRepository | `get_all()`, `get_by_id(id)` |
| TaskRepository | `get_all()`, `get_by_id(id)` |

---

# MockRepository

要求：

- 继续使用现有 Mock 数据
- 禁止复制新的 Mock 数据
- 实现 Repository Interface

---

# Service Layer

新增 Service：

| Service | 说明 |
|---------|------|
| device_service | 调用 DeviceRepository |
| resource_service | 调用 ResourceRepository |
| operation_service | 调用 OperationRepository |
| task_service | 调用 TaskRepository |

Service 只负责调用 Repository。

---

# API Migration

/api/v1/* 改为：

```
API Layer
    ↓
Service Layer
    ↓
Repository Layer
```

---

# 禁止

- Database
- ORM
- SQLite
- PostgreSQL
- 删除 Store
- 修改前端

---

# Technical Debt

- server.py Mock 数据迁移到 Repository

---

# Output

完成后输出：

1. 修改文件
2. 新增文件
3. 测试结果
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。
