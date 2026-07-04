\# Sprint002 - Workspace Foundation



Version: 1.0



Status: Ready



\---



\# Objective



建立 WorkOps 的 Workspace（工作台）。



Workspace 是用户进入系统后的首页。



本 Sprint 目标：



建立完整产品体验。



不连接任何真实设备。



全部使用 Mock Data。



\---



\# Scope



允许：



\- Workspace 页面

\- 左侧导航

\- 顶部 Header

\- Mock Widgets

\- 响应式布局

\- 中英文支持



禁止：



\- SQLite

\- SSH

\- WinRM

\- Docker

\- PVE

\- PBS

\- 自动发现

\- Backup

\- Restore

\- Cloud Sync



全部使用 Mock。



\---



\# Workspace Layout



左侧导航：



\- 工作台

\- 设备

\- 资源

\- 操作

\- 任务

\- 监控

\- 远程

\- AI

\- 设置



顶部：



\- WorkOps Logo

\- 当前语言

\- 搜索（占位）

\- 通知（占位）



主体：



Dashboard 风格。



\---



\# Widgets



\## Device Summary



显示：



\- 总设备数

\- 在线设备

\- 离线设备

\- 告警数量



Mock。



\---



\## Recent Operations



显示最近操作。



例如：



\- Backup Success

\- Snapshot Completed

\- Restore Finished



Mock。



\---



\## Monitoring Overview



显示：



\- CPU

\- Memory

\- Storage

\- Network



Mock。



\---



\## Alerts



显示：



\- SMART Warning

\- Backup Failed

\- Disk Warning



Mock。



\---



\## Quick Actions



按钮：



\- 添加设备

\- 新建操作

\- 查看任务



按钮无需实现业务逻辑。



\---



\# UI Requirements



默认中文。



支持 English。



所有新增文字必须使用：



WorkOps.t()



禁止写死字符串。



\---



\# Mobile



支持：



\- 响应式布局

\- 折叠菜单

\- 卡片布局



\---



\# Out of Scope



本 Sprint 禁止：



\- Device CRUD

\- Resource CRUD

\- Operation CRUD

\- Task CRUD

\- Backup

\- Restore

\- Remote

\- Discover

\- Import

\- Export



\---



\# Acceptance



完成后必须满足：



\- Workspace 可正常显示

\- 左侧导航正常

\- Mock Widgets 正常

\- 中英文切换正常

\- 移动端正常

\- 不连接任何真实设备



\---



\# Output



完成后输出：



1\. 修改文件列表

2\. 新增文件列表

3\. 页面截图（如可提供）

4\. 用户测试项



完成后立即停止。



不得进入 Sprint003。

