# Sprint010 - Unified Store Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 Unified Store Foundation。

Unified Store 负责统一管理 Mock 数据来源。

本 Sprint 不接数据库。

不接 API。

不连接真实设备。

只把当前分散在各模块中的 Mock 数据，逐步集中到 static/stores/。

---

# Goals

- 建立 Unified Store 目录结构
- 建立 Device Store
- 建立 Resource Store
- 建立 Operation Store
- 建立 Task Store
- 建立 Monitor Store
- 建立 Store Index（统一入口）
- 各模块从 Store 读取数据

---

# Scope

允许创建：

- static/stores/device-store.js
- static/stores/resource-store.js
- static/stores/operation-store.js
- static/stores/task-store.js
- static/stores/monitor-store.js
- static/stores/index.js

禁止：

- SQLite
- API
- 真实扫描
- 真实监控
- 真实执行
- 业务逻辑重构
- UI 改版

---

# Store 设计原则

每个 Store 负责：

- 管理自己的 Mock 数据
- 提供 getAll() 方法
- 提供 getById() 方法
- 不暴露原始数组引用

Store 不负责：

- 业务逻辑
- UI 渲染
- API 调用
- 数据持久化

---

# Mock 数据迁移

从以下模块迁移 Mock 数据：

| 模块 | 迁移到 |
|------|--------|
| device-registry.js | stores/device-store.js |
| resource-registry.js | stores/resource-store.js |
| operation-engine.js | stores/operation-store.js |
| task-engine.js | stores/task-store.js |
| monitoring-engine.js | stores/monitor-store.js |

迁移后：

- 各模块删除内部 MOCK_*_STORE
- 各模块从 Store 读取数据
- 各模块渲染逻辑不变

---

# Module Constraints

Store 模块：

- 通过 window.DeviceStore / window.ResourceStore 等暴露
- 只暴露 getAll() 和 getById()
- 不暴露原始数组

业务模块：

- 从 Store 读取数据
- 渲染逻辑不变
- 不修改 Store

---

# Existing Modules

必须保持兼容：

- Workspace
- Device Registry
- Resource Registry
- Operation Engine
- Task Engine
- Monitoring Engine
- Backup
- Restore
- NAS
- Windows
- Cloud
- PVE
- Jobs

不得删除。

不得重构。

不得修改业务逻辑。

不得修改 UI。

---

# Out Of Scope

本 Sprint 禁止：

- SQLite / 数据库
- API
- 真实扫描
- 真实监控
- 真实执行
- 业务逻辑重构
- UI 改版
- 新增页面
- 新增组件

---

# Acceptance

完成后必须满足：

✓ 所有 Mock 数据集中在 static/stores/
✓ 各模块从 Store 读取数据
✓ 各模块渲染逻辑不变
✓ UI 不变
✓ 功能不变
✓ i18n 正常
✓ Mobile 正常

---

# Output

完成后输出：

1. 新增文件
2. 修改文件
3. 数据迁移清单
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。

不得进入 Sprint011。
