# Sprint006 - Task Engine Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps Task Engine。

Task 是 Operation 的执行实例。

Task 不负责执行命令。

Task 负责：

- 生命周期
- 状态
- 执行历史
- 执行结果（Mock）

全部使用 Mock Data。

禁止连接真实设备。

---

# Goals

- 建立 Task Engine 页面
- 建立 Task Card
- 建立 Task Timeline
- 建立 Task Selector
- 建立 Mock Task Store
- 建立 Status Badge
- 不修改已有模块

---

# Scope

允许：

- Task Engine 页面
- Task Card
- Task Timeline
- Task Selector
- Mock Task Store
- Status Badge
- 响应式布局
- i18n

禁止：

- SSH
- API
- SQLite
- Docker
- PVE API
- Windows API
- Backup 真执行
- Restore 真执行

---

# Task Fields

仅允许：

- id
- operation_id
- operation_name
- device_name
- resource_name
- status
- start_time
- end_time
- duration
- result

不得新增字段。

---

# Task Status

任务状态：

- pending - 等待中
- running - 执行中
- success - 成功
- failed - 失败
- cancelled - 已取消

---

# Mock Task Store

任务示例：

- Daily Backup (op-001)
  - Task 2026-07-04 02:00 → success
  - Task 2026-07-03 02:00 → success
  - Task 2026-07-02 02:00 → failed
- NAS Photos Backup (op-002)
  - Task 2026-07-01 03:00 → success
- Daily Snapshot (op-003)
  - Task 2026-07-04 01:00 → success
  - Task 2026-07-03 01:00 → success
- Cloud Sync (op-005)
  - Task 2026-07-04 05:00 → success
  - Task 2026-07-03 05:00 → running
- Data Migration (op-007)
  - Task 2026-07-04 10:00 → pending

全部 Mock。

不得读取真实系统。

---

# Module Constraints

MOCK_TASK_STORE 必须保持模块私有。

不得暴露 getTasks()。

window.TaskEngineModule 只允许暴露：

- render
- renderTaskCard
- renderTaskSelector

---

# UI

建立 Task Engine 页面。

显示：

- 任务名称（关联 Operation）
- 状态（StatusBadge）
- 开始时间
- 结束时间
- 持续时间
- 执行结果

建立 Task Timeline 组件。

显示最近任务的时间线。

建立 Task Selector 组件。

本 Sprint 只提供组件。

暂不接入旧页面。

---

# i18n

所有新增文字必须使用：

WorkOps.t()

key 命名空间使用：

- task.*
- task.status.*

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
- Operation Engine
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

- Task CRUD
- Task Detail
- Task Scheduler
- Task Executor
- 真实命令执行
- SSH / PVE / Docker 连接
- Operation Engine 修改

---

# Acceptance

完成后必须满足：

✓ Workspace 不受影响
✓ Device Registry 不受影响
✓ Resource Registry 不受影响
✓ Operation Engine 不受影响
✓ Task Engine 正常
✓ Task Card 正常
✓ Task Timeline 正常
✓ Task Selector 可显示
✓ Status Badge 正常
✓ Mock 数据正常
✓ i18n 正常
✓ Mobile 正常
✓ 不连接真实设备
✓ 不执行任何命令

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

不得进入 Sprint007。
