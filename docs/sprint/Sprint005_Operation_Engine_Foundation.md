# Sprint005 - Operation Engine Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps 的 Operation Engine（操作引擎）。

Operation Engine 是整个 WorkOps 的统一操作管理入口。

本 Sprint 不执行任何真实操作。

全部使用 Mock Data。

---

# Goals

- 建立 Operation Engine 页面
- 建立 Operation Card
- 建立 Operation Selector
- 建立 Operation Type Badge
- 建立 Mock Operation Store
- 不修改已有模块

---

# Scope

允许：

- Operation Engine 页面
- Operation Card
- Operation Selector
- Operation Type Badge
- Mock Operation Store
- i18n 支持
- 响应式布局

禁止：

- SQLite
- API
- SSH
- ZFS
- PVE API
- OMV API
- Docker
- 自动发现
- 真实扫描
- Backup 执行
- Restore 执行
- Snapshot 执行
- Cloud Sync 执行

全部使用 Mock。

---

# Operation Fields

字段遵循 `docs/05_DATA_MODEL.md`。

本 Sprint Mock 数据只用于展示：

- id
- device_id
- device_name
- resource_id
- resource_name
- name
- type
- schedule
- last_run
- status

不得新增字段。

---

# Operation Types

操作类型：

- backup - 备份
- restore - 恢复
- snapshot - 快照
- migration - 迁移
- verify - 验证
- cloud_sync - 云同步

---

# Mock Operation Store

操作示例：

- Windows-PC
  - Daily Backup (backup)
- NAS-01
  - NAS Photos Backup (backup)
  - Daily Snapshot (snapshot)
  - Backup Verify (verify)
  - Cloud Sync (cloud_sync)
- Linux-Server
  - Test Restore (restore)
- PVE
  - Data Migration (migration)

全部 Mock。

不得读取真实系统。

---

# Module Constraints

MOCK_OPERATION_STORE 必须保持模块私有。

不得暴露 getOperations()。

window.OperationEngineModule 只允许暴露：

- render
- renderOperationCard
- renderOperationSelector

---

# OperationTypeBadge

保持简单。

只显示文字标签：

- Backup
- Restore
- Snapshot
- Migration
- Verify
- Cloud Sync

不要增加：

- Icon
- Tooltip
- Progress
- Menu

---

# UI

建立 Operation Engine 页面。

显示：

- 操作名称
- 操作类型（OperationTypeBadge）
- 状态（StatusBadge）
- 关联资源
- 调度方式
- 最后执行时间

建立 Operation Selector 组件。

本 Sprint 只提供组件。

暂不接入旧页面。

---

# i18n

所有新增文字必须使用：

WorkOps.t()

key 命名空间使用：

- operation.*
- operation.type.*
- operation.status.*

不得修改已有 key。

---

# Mobile

保持 Sprint002 响应式布局。

不得新增移动端逻辑。

---

# Existing Modules

必须保持兼容：

- Workspace
- Device Registry
- Resource Registry
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

- Operation CRUD
- Operation Detail
- Operation Scheduler
- Operation Executor
- Operation History
- Task Engine
- 真实 Backup / Restore / Snapshot 执行
- SSH / PVE / Docker 连接

---

# Acceptance

完成后必须满足：

✓ Workspace 不受影响
✓ Device Registry 不受影响
✓ Resource Registry 不受影响
✓ Operation Engine 正常
✓ Operation Card 正常
✓ Operation Selector 可显示
✓ Operation Type Badge 正常
✓ Status Badge 正常
✓ Mock 数据正常
✓ i18n 正常
✓ Mobile 正常
✓ 不连接真实设备
✓ 不执行任何操作

---

# Output

完成后输出：

1. 修改文件
2. 新增文件
3. Mock 数据结构
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。

不得进入 Sprint006。
