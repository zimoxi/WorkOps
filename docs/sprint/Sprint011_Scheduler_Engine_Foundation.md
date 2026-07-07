# Sprint011 - Scheduler Engine Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 Scheduler Engine。

Scheduler 负责：

- Operation 调度计划
- Schedule Card
- Schedule Selector
- Schedule Summary
- Mock Schedule Store

Scheduler 不负责：

- 真正执行任务
- Cron
- Timer
- 后台服务
- API
- SSH
- Docker

---

# Goals

- 建立 Scheduler Dashboard
- 建立 Schedule Card
- 建立 Schedule Summary
- 建立 Schedule Selector
- 建立 Mock Schedule Store
- 使用 Components

---

# Scope

允许：

- Mock Schedule Store
- Schedule Card
- Schedule Summary
- Components
- StatusBadge

禁止：

- SQLite
- API
- Cron
- Timer
- 后台线程
- 真执行
- Notification

---

# Schedule Fields

仅允许：

- id
- operation_id
- operation_name
- schedule_type
- expression
- next_run
- enabled

不得新增字段。

---

# Schedule Types

调度类型：

- daily - 每天
- weekly - 每周
- monthly - 每月
- manual - 手动

---

# Mock Schedule Store

调度示例：

- Daily Backup → daily → 02:00 → enabled
- NAS Photos Backup → weekly → sunday 03:00 → enabled
- Daily Snapshot → daily → 01:00 → enabled
- Backup Verify → weekly → saturday 04:00 → enabled
- Cloud Sync → daily → 05:00 → enabled
- Data Migration → manual → - → disabled

全部 Mock。

不得读取真实系统。

---

# Module Constraints

MOCK_SCHEDULE_STORE 必须保持模块私有。

不得暴露 getSchedules()。

window.SchedulerEngineModule 只允许暴露：

- render

---

# UI

建立 Scheduler Dashboard 页面。

显示：

- Schedule Summary（启用/禁用/总数统计）
- Schedule Card（调度计划卡片）
- Schedule Selector（调度选择器预览）

使用 Components。

---

# i18n

所有新增文字必须使用：

WorkOps.t()

key 命名空间使用：

- scheduler.*
- scheduler.type.*
- scheduler.status.*

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

---

# Out Of Scope

本 Sprint 禁止：

- 真正执行任务
- Cron / Timer
- 后台服务
- API
- SSH / Docker
- Notification
- 修改 Architecture
- 修改 Data Model
- 修改 UI

---

# Acceptance

完成后必须满足：

✓ Workspace 不受影响
✓ Device Registry 不受影响
✓ Resource Registry 不受影响
✓ Operation Engine 不受影响
✓ Task Engine 不受影响
✓ Monitoring Engine 不受影响
✓ Scheduler Dashboard 正常
✓ Schedule Card 正常
✓ Schedule Summary 正常
✓ Schedule Selector 可显示
✓ Mock 数据正常
✓ i18n 正常
✓ Mobile 正常
✓ 不执行任何任务

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

不得进入 Sprint012。
