# Sprint020 — Persistence Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps Persistence Foundation。

将 M3 的：

```
Service
    ↓
Repository Interface
    ↓
MockRepository
```

扩展为：

```
Service
    ↓
Repository Interface
    ├── MockRepository
    └── DatabaseRepository
```

本 Sprint 只建立可替换的持久化基础，不迁移全部业务模块。

---

# Core Principles

1. Repository Interface 保持数据源无关。

2. Service 不得直接访问数据库。

3. API 不得直接访问数据库。

4. DatabaseRepository 与 MockRepository 必须可以替换。

5. 数据库选择和连接配置不得散落在业务代码中。

6. Migration 必须可升级、可回滚。

7. 本 Sprint 不连接真实设备，不执行真实任务。

---

# 本 Sprint 范围

优先建立：

- Persistence Configuration
- Database Connection Factory
- Schema Version
- Migration Runner 基础
- DatabaseRepository 基础接口
- Session 持久化设计
- Task 持久化设计
- ExecutionResult 持久化设计
- Repository Provider / Factory
- 测试数据库隔离
- Windows 文件句柄安全关闭

---

# 最小迁移范围

本 Sprint 不得一次迁移所有模块。

优先选择最小验证实体：

- Task
- ExecutionResult

用于验证：

```
Service
    ↓
Repository
    ↓
DatabaseRepository
    ↓
SQLite Test Database
```

Device、Resource、Operation、Monitor、Schedule 暂不强制迁移。

---

# 数据库边界

## 允许

- SQLite 作为本地开发和测试实现
- Repository Interface
- DatabaseRepository
- 显式连接关闭
- 事务边界
- Schema Version
- Migration Up / Down
- 临时测试数据库

## 禁止

- ORM
- PostgreSQL 绑定
- MySQL 绑定
- SQL Server 绑定
- 自动创建生产数据库
- 在 import 时连接数据库
- 全局长期 SQLite connection
- 数据库连接写入前端
- 数据库密码写入 Git

---

# Session Persistence

本 Sprint 只设计或建立最小存储边界。

必须明确：

- Session ID
- User ID
- Created At
- Expires At
- Revoked At

禁止存储：

- 明文密码
- Cookie 原文
- Token 原文
- SSH 凭据

是否实际迁移现有内存 Session，必须由 Architecture Review 决定，不能默认实施。

---

# Task Persistence

Task 状态只允许：

```
pending
running
success
failed
cancelled
```

必须保持现有合法状态转换规则。

DatabaseRepository 不得绕过：

```python
transition_status(
    task_id,
    expected_status,
    new_status
)
```

必须支持条件状态更新，避免错误转换。

---

# ExecutionResult Persistence

字段必须保持 Sprint018 已冻结的 9 个字段：

- task_id
- status
- started_at
- finished_at
- duration
- stdout
- stderr
- exit_code
- message

不得新增敏感字段。

不得保存：

- 密码
- 私钥
- Token
- Cookie
- Session ID
- 完整连接字符串
- 原始敏感异常文本

---

# Migration 要求

必须设计：

- schema_version
- upgrade()
- downgrade()
- 事务失败回滚
- 重复运行安全
- 空数据库初始化
- 已存在数据库升级
- 回滚后的数据处理说明

## 禁止

- 不可逆删除数据而无说明
- import 时自动迁移
- 静默吞掉 Migration 错误

---

# 连接生命周期

必须遵循 Sprint019 修复结果：

- 每次 SQLite 操作后显式关闭连接
- 使用 contextmanager
- 不保留全局长期 connection
- Windows 下数据库文件必须可删除
- close() 必须幂等
- 测试必须使用临时目录
- 不使用 sleep 或 gc.collect() 掩盖文件锁

---

# Mock 与 Database 共存

必须支持：

```
Mock 模式：
RepositoryProvider → MockRepository

Database 模式：
RepositoryProvider → DatabaseRepository
```

切换方式必须集中管理。

禁止在 Service 中写：

```python
if database:
if mock:
```

Service 只能依赖 Repository Interface。

---

# 禁止

- 真实设备连接
- SSH
- WinRM
- SNMP
- 真实执行
- Backup
- Restore
- Execution API
- Credential Management
- 修改前端
- 修改权限矩阵
- 修改 Task Data Model
- 大规模重构 server.py
- 一次迁移全部 Store
- 提前实现 Sprint021 内容

---

# Test Requirements

必须包含：

- 空数据库初始化
- Schema Version
- Migration upgrade
- Migration downgrade
- 重复 migration
- Migration 失败回滚
- DatabaseRepository get_all/get_by_id
- Task transition_status 合法转换
- Task transition_status 非法转换
- ExecutionResult 保存与读取
- MockRepository 仍可工作
- RepositoryProvider 切换
- 数据库连接正确关闭
- Windows 临时数据库可删除
- 不持久化敏感字段
- Full Suite 保持通过

---

# 完成标准

1. Mock 模式保持兼容。
2. DatabaseRepository 最小链路可测试。
3. 不连接真实设备。
4. 不新增真实执行能力。
5. Full Suite 连续通过。
6. Migration 可升级和回滚。
7. Windows 无 SQLite 文件锁。
8. 不修改任何 static/*.js。

---

# Technical Debt

| ID | 说明 | 状态 |
|----|------|------|
| TD-055 | Device/Resource/Operation 迁移到 DatabaseRepository | 待后续 Sprint |
| TD-056 | Session 仍为内存存储，需要在后续认证安全或专门持久化阶段处理；不默认归入 Sprint021 Credential Management | 待后续 Sprint |
