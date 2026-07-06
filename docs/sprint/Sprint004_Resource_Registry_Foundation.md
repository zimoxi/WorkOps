# Sprint004 - Resource Registry Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps 的 Resource Registry（资源注册中心）。

Resource Registry 是设备资源的统一目录。

本 Sprint 不连接真实设备。

全部使用 Mock Data。

---

# Goals

- 新增 Resource Registry 页面
- 新增 Resource Card
- 新增 Resource Selector
- 新增 Mock Resource Store
- 资源必须关联 Device
- 不修改现有 Backup / Restore / NAS / Windows / Cloud / PVE / Jobs 逻辑

---

# Scope

允许：

- Resource Registry 页面
- Resource Card
- Resource Selector
- Mock Resource Store
- i18n 文案
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
- Backup / Restore 执行

---

# Resource Fields

字段遵循 `docs/05_DATA_MODEL.md`。

本 Sprint Mock 数据只允许使用：

- id
- device_id
- name
- type
- path
- mount_point
- size_total
- size_used
- status

不得新增字段。

---

# Mock Resource Store

资源示例：

- Windows-PC
  - Disk C
  - Disk D
  - Folder D:\Backup
- NAS-01
  - Pool tank
  - Dataset tank/photos
  - Share backup
- PVE
  - VM 101
  - VM 102
  - Storage local-lvm
- OMV
  - Share data
  - Share media

全部 Mock。

不得读取真实系统。

---

# UI

新增 Resource Registry 页面。

显示：

- 资源名称
- 所属设备
- 类型
- 路径 / 挂载点
- 容量使用
- 状态

新增 Resource Selector 组件。

本 Sprint 只预览，不接入旧页面。

---

# i18n

所有新增文案必须使用：

WorkOps.t()

新增 key 建议使用：

- registry.resource.*
- resource.*
- resource.status.*

不得修改已有 key。

---

# Mobile

必须支持移动端。

卡片在移动端单列显示。

不得破坏 Sprint002 / Sprint003 响应式布局。

---

# Existing Modules

必须保持兼容：

- Workspace
- Device Registry
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

# Out of Scope

本 Sprint 不做：

- Resource CRUD
- Resource Detail
- Resource Discovery
- Storage Discovery
- ZFS 读取
- df 读取
- API
- 数据库
- 与 Backup 页面集成

---

# Acceptance

完成后必须满足：

- Workspace 正常
- Device Registry 正常
- Resource Registry 正常
- Resource Card 正常
- Resource Selector 正常
- Mock 数据正常
- i18n 正常
- Mobile 正常
- 旧模块不受影响

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

不得进入 Sprint005。