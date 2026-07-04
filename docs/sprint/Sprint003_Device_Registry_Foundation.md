\# Sprint003 - Device Registry Foundation



Version: 1.0



Status: Ready



Priority: High



\---



\# Objective



建立 WorkOps 的 Device Registry（设备注册中心）。



Device Registry 是整个 WorkOps 的设备目录（Source of Devices）。



所有模块（Backup、Restore、Remote、Monitoring 等）以后都引用 Device Registry。



本 Sprint 不连接真实设备。



全部使用 Mock Data。



\---



\# Goals



建立统一 Device Registry。



建立 Device Selector。



建立 Device Status Badge。



建立 Mock Device Source。



不修改已有 Backup 功能。



\---



\# Scope



允许：



\- Device Registry 页面

\- Device Selector 组件

\- Device Status Badge

\- Mock Device Store

\- Device Card



禁止：



\- SSH

\- Ping

\- WinRM

\- Docker

\- PVE API

\- 自动发现

\- Backup

\- Restore

\- Monitoring

\- SQLite



全部使用 Mock。



\---



\# Existing Modules



以下模块必须保持兼容：



\- Backup

\- Restore

\- NAS

\- Windows

\- PVE

\- Cloud

\- Jobs



不得删除。



不得重构。



不得修改业务逻辑。



\---



\# Device Registry



建立统一设备目录。



字段：



\- UUID

\- Name

\- Type

\- Status

\- Primary IP



全部来自：



docs/05\_DATA\_MODEL.md



不得新增字段。



\---



\# Device Selector



新增统一组件：



DeviceSelector



以后：



所有需要选择设备的页面：



统一使用。



本 Sprint：



只提供组件。



暂不接入旧页面。



\---



\# Device Status Badge



新增统一状态组件。



状态：



\- Online

\- Offline

\- Warning

\- Unknown



以后：



整个 WorkOps 共用。



\---



\# Mock Device Store



建立：



workspace\_devices



Mock 数据：



Windows-PC



Linux-Server



NAS-01



OMV



PVE



PBS



Router



全部静态。



\---



\# Frontend



新增：



Device Registry 页面。



显示：



\- 名称

\- 类型

\- IP

\- 状态



点击无动作。



不进入详情。



\---



\# UI



保持：



Workspace 风格。



支持：



中文



English



所有文字：



使用：



WorkOps.t()



\---



\# Mobile



保持 Sprint002 响应式布局。



不得新增新的移动端逻辑。



\---



\# Out Of Scope



本 Sprint 禁止：



\- CRUD

\- SQLite

\- API

\- Device Detail

\- Device Monitor

\- Device Remote

\- 自动发现

\- Backup Integration



以后 Sprint 再做。



\---



\# Acceptance



完成后必须满足：



✓ Workspace 不受影响



✓ Device Registry 正常



✓ Device Selector 可显示



✓ Status Badge 正常



✓ Mock 数据正常



✓ i18n 正常



✓ Mobile 正常



\---



\# Output



完成后输出：



1\. 修改文件



2\. 新增文件



3\. Mock 数据结构



4\. 用户测试项



完成后立即停止。



不得进入 Sprint004。

