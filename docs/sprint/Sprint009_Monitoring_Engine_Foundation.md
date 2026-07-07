# Sprint009 - Monitoring Engine Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 Monitoring Engine。

Monitoring 负责：

- 展示系统运行状态
- 聚合 Device / Resource / Operation / Task 的 Mock 数据
- Dashboard Widget
- Health Status
- Summary View

Monitoring 不负责：

- 修改数据
- 执行任务
- 调度任务

---

# Goals

- 建立 Monitoring Dashboard
- 建立 Health Card
- 建立 Summary Card
- 建立 Monitor Widget
- 建立 Mock Monitor Store
- 建立 Status Badge
- 使用 Components

---

# Scope

允许：

- Monitoring Dashboard
- Health Card
- Summary Card
- Monitor Widget
- Mock Monitor Store
- Status Badge
- Components

禁止：

- API
- SQLite
- SSH
- Docker
- PVE API
- Backup 真执行
- Scheduler
- Notification

---

# Monitor Fields

仅允许：

- id
- target_type
- target_name
- status
- message
- updated_at

不得新增字段。

---

# Target Types

监控目标类型：

- device - 设备
- resource - 资源
- operation - 操作
- task - 任务

---

# Mock Monitor Store

监控示例：

- Device Health
  - Windows-PC → online
  - Linux-Server → online
  - NAS-01 → online
  - PVE → warning
  - PBS → offline

- Resource Health
  - Disk C → online
  - Pool tank → online
  - VM 101 → online

- Operation Health
  - Daily Backup → success
  - Cloud Sync → running

- Task Health
  - task-001 → success
  - task-008 → running

全部 Mock。

不得读取真实系统。

---

# Module Constraints

MOCK_MONITOR_STORE 必须保持模块私有。

不得暴露 getMonitors()。

window.MonitoringEngineModule 只允许暴露：

- render

---

# UI

建立 Monitoring Dashboard 页面。

显示：

- System Health Summary（设备在线/离线/警告统计）
- Device Health Card（设备健康状态）
- Resource Health Card（资源健康状态）
- Operation Health Card（操作健康状态）
- Task Health Card（任务健康状态）
- Monitor Widget（综合监控面板）

使用 Components。

---

# i18n

所有新增文字必须使用：

WorkOps.t()

key 命名空间使用：

- monitor.*
- monitor.status.*

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

- 真实监控
- 真实数据采集
- SSH / SNMP / API 连接
- Scheduler
- Notification
- 修改 Architecture
- 修改 Data Model

---

# Acceptance

完成后必须满足：

✓ Workspace 不受影响
✓ Device Registry 不受影响
✓ Resource Registry 不受影响
✓ Operation Engine 不受影响
✓ Task Engine 不受影响
✓ Monitoring Dashboard 正常
✓ Health Card 正常
✓ Summary Card 正常
✓ Monitor Widget 正常
✓ Mock 数据正常
✓ i18n 正常
✓ Mobile 正常
✓ 不连接真实系统
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

不得进入 Sprint010。
