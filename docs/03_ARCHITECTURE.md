\# WorkOps Architecture



Version: 1.1



Status: Active



Last Updated: 2026-07-03



\---



\# 1. Overview



WorkOps 是一个统一管理个人、家庭实验室（HomeLab）以及小型办公环境（SOHO）基础设施的平台。



WorkOps 采用 Device First 架构。



Device 是整个系统唯一根实体（Root Entity）。



所有资源、操作、任务、监控最终都属于某个 Device。



\---



\# 2. Design Principles



整个系统遵循以下原则：



\- Device First

\- Security First

\- Mobile First

\- Local First

\- Documentation First

\- AI Assisted

\- Offline First



\---



\# 3. Core Domain



WorkOps 只有五个核心领域。



\## Device



表示一个可以管理的设备。



例如：



\- Windows

\- Linux

\- PVE

\- PBS

\- OMV

\- NAS

\- Router



Device 是整个系统唯一根实体。



所有对象最终必须关联到 Device。



Device 可以拥有多个 Capability。



例如：



\- SSH

\- SMB

\- RDP

\- Docker

\- WinRM

\- HTTPS API



Capability 不是 Domain。



只是 Device 支持的能力。



\---



\## Resource



Resource 表示 Device 拥有的数据资源。



例如：



\- Disk

\- Folder

\- Dataset

\- Pool

\- VM

\- Container

\- Share



Resource 必须属于某个 Device。



\---



\## Operation



Operation 表示一次用户发起的操作。



例如：



\- Backup

\- Restore

\- Snapshot

\- Verify

\- Migration

\- Cloud Sync



Operation 不直接执行。



Operation 创建 Task。



\---



\## Task



Task 是 Operation 的执行实例。



Task 保存：



\- 状态

\- 日志

\- 开始时间

\- 结束时间

\- 返回结果



Task 永远属于一个 Operation。



\---



\## Monitor



Monitor 表示设备运行状态。



例如：



\- CPU

\- Memory

\- Disk

\- Temperature

\- SMART

\- Network



Monitor 不负责执行任何操作。



\---



\# 4. Domain Relationship



WorkOps



└── Device



&#x20;   ├── Resources



&#x20;   ├── Operations



&#x20;   │      │



&#x20;   │      └── Tasks



&#x20;   ├── Monitoring



&#x20;   └── Capabilities



Device 是唯一 Root Entity。



任何对象都必须能够追溯到 Device。



\---



\# 5. Module Architecture



WorkOps 一级导航固定如下：



\- 工作台（Workspace）

\- 设备（Devices）

\- 资源（Resources）

\- 操作（Operations）

\- 任务（Tasks）

\- 监控（Monitoring）

\- 远程（Remote）

\- AI

\- 设置（Settings）



一级菜单代表业务领域，而不是功能。



Backup、Restore、Cloud Sync 都属于 Operations。



\---



\# 6. Operation Lifecycle



所有 Operation 必须遵循统一生命周期：



Generate



↓



Preview



↓



Confirm



↓



Execute



↓



Log



↓



Notify



任何危险操作必须经过 Confirm。



\---



\# 7. Layer Architecture



Presentation



↓



Application



↓



Domain



↓



Infrastructure



↓



Platform



Presentation 不允许直接访问数据库。



Presentation 不允许直接执行系统命令。



\---



\# 8. Future



未来规划：



\- Plugin System

\- Multi User

\- RBAC

\- Automation

\- AI Assistant



所有新增能力必须保持向后兼容。



\---



\# 9. Architecture Rules



任何新增功能必须回答：



1\. 属于哪个 Device？

2\. 属于哪个 Domain？

3\. 是否创建 Operation？

4\. 是否创建 Task？

5\. 是否需要 Monitor？



无法回答，则不得开发。



\---



\# 10. Source of Truth



Project Charter



↓



Architecture



↓



Data Model



↓



Sprint



↓



Implementation



文档是真相（Source of Truth）。



代码是文档的实现。

