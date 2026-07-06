# Sprint008 - API Cleanup and Module Simplification

Version: 1.0

Status: Ready

---

# Objective

完成 M2 前的平台清理工作。

删除 Sprint007 保留的兼容层。

统一所有模块调用 Components。

不新增业务。

---

# Goals

- 删除 Sprint007 保留的兼容层函数
- 统一所有模块调用 Components API
- 简化模块调用
- 清理重复代码
- 更新引用

---

# Scope

允许修改：

- 删除兼容层函数
- 统一 Components API
- 简化模块调用
- 清理重复代码
- 更新引用

禁止：

- 不新增业务
- 不修改 UI
- 不修改 Architecture
- 不修改 Data Model
- 不修改 Mock Data
- 不修改页面布局

---

# Compatibility Layer Cleanup

Sprint007 保留的兼容层函数，本 Sprint 删除：

## device-registry.js

删除：

- renderStatusBadge() 内部实现
- renderDeviceCard() 内部实现
- renderDeviceSelector() 内部实现

改为直接调用：

- Components.renderStatusBadge()
- Components.renderCard()
- Components.renderSelector()

## resource-registry.js

删除：

- renderStatusBadge() 内部实现
- renderResourceCard() 内部实现
- renderResourceSelector() 内部实现

改为直接调用：

- Components.renderStatusBadge()
- Components.renderCard()
- Components.renderSelector()

## operation-engine.js

删除：

- renderStatusBadge() 内部实现
- renderOperationCard() 内部实现
- renderOperationSelector() 内部实现

保留：

- renderOperationTypeBadge()（Operation 特有，不迁移）

## task-engine.js

删除：

- renderStatusBadge() 内部实现
- renderTaskCard() 内部实现
- renderTaskSelector() 内部实现

保留：

- renderTaskTimeline()（Timeline 保持内部实现）

---

# Module Constraints

删除兼容层后：

- 各模块直接调用 Components API
- 不再保留降级方案
- Components 未加载时报错（开发阶段即可发现）

---

# Existing Modules

必须保持功能一致：

- Workspace
- Device Registry
- Resource Registry
- Operation Engine
- Task Engine
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

---

# Out Of Scope

本 Sprint 禁止：

- 新增业务功能
- 新增页面
- 新增组件
- 修改 UI
- 修改 Architecture
- 修改 Data Model
- 修改 Mock Data
- 修改页面布局

---

# Acceptance

完成后必须满足：

✓ Workspace 功能一致
✓ Device Registry 功能一致
✓ Resource Registry 功能一致
✓ Operation Engine 功能一致
✓ Task Engine 功能一致
✓ 所有模块直接调用 Components
✓ 无兼容层代码
✓ 无重复代码
✓ i18n 正常
✓ Mobile 正常

---

# Output

完成后输出：

1. 修改文件
2. 删除代码清单
3. 验证结果
4. 用户测试项
5. Technical Debt

完成后立即停止。

不得进入 Sprint009。
