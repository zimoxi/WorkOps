\# WorkOps Project State



Version: 0.4.0



Status: Active Development



Last Updated: 2026-07-04



\---



\# Project Baseline



Foundation Baseline:



v0.2.0-foundation



Current Release:



v0.3.0-device-registry



\---



\# Current Stage



Current Phase:



Foundation



Current Sprint:



Sprint005 - Operation Engine Foundation



Current Status:



Planning



\---



\# Product Vision



WorkOps 是统一基础设施运维平台（Unified Infrastructure Operations Platform）。



目标：



一个 Web 控制台统一管理：



\- Windows

\- Linux

\- NAS

\- OMV

\- PVE

\- PBS

\- Docker

\- Backup

\- Restore

\- Monitoring

\- Remote

\- Automation

\- AI Assistant



\---



\# Architecture



Architecture Status:



Frozen



Current Architecture Version:



1.1



Current Data Model Version:



1.0



Core Domains:



\- Device

\- Resource

\- Operation

\- Task

\- Monitor



Device 是唯一 Root Entity。



禁止修改：



\- Architecture

\- Data Model



如确需修改：



Architecture Decision Required



\---



\# Completed



✅ Project Charter



✅ Product Backlog



✅ Architecture



✅ Data Model



✅ AI Guard



✅ Workspace Foundation



✅ Device Registry Foundation



✅ Resource Registry Foundation



\---



\# Current Sprint



Sprint004



名称：



Resource Registry Foundation



目标：



建立统一 Resource Registry。



包含：



\- Resource Registry 页面

\- Resource Card

\- Resource Selector

\- Mock Resource Store



全部使用 Mock。



不得连接真实设备。



\---



\# Next Sprint



Sprint005



Operation Engine Foundation



\---



\# Existing Modules



当前模块：



\- Workspace

\- Device Registry

\- Backup

\- Restore

\- NAS

\- Windows

\- Cloud

\- PVE

\- Jobs



所有模块必须保持兼容。



不得删除。



不得重构。



\---



\# Coding Rules



开发必须遵循：



AI\_GUARD.md



必须：



\- Small Diff

\- Mock First

\- Backward Compatible

\- One Sprint At A Time



禁止：



\- Rewrite

\- Large Refactor

\- Cross Sprint Development

\- 修改 Architecture

\- 修改 Data Model



\---



\# AI Workflow



AI 工作流程：



1\. 阅读 AI\_GUARD.md

2\. 阅读 PROJECT\_STATE.md

3\. 阅读当前 Sprint

4\. 输出 Implementation Plan

5\. 等待 Review

6\. Coding

7\. Sprint Review

8\. 更新 PROJECT\_STATE.md



不得跳步骤。



\---



\# Review Status



Sprint001



PASS



Sprint002



PASS



Sprint003



PASS WITH NOTES



Sprint004



PASS


Planning



\---



\# Technical Debt



\## TD-001



server.py



INDEX\_HTML 仍然较大。



建议：



后续拆分模板。



Priority:



Medium



\---



\## TD-002



static/app.js



文件仍然较大。



建议：



逐 Sprint 模块化。



Priority:



High



\---



\## TD-003



Mock Data



目前仍然分散。



未来统一迁移至 Device Store / Resource Store。



Priority:



Medium



\---



\## TD-004



renderDevices()



旧 Device CRUD 保留但未使用。



未来决定：



\- 删除

\- 恢复

\- 整合



Priority:



Low



\---



\## TD-005



workspace.js 与 device-registry.js



分别维护 Mock 数据。



未来建立统一 Store。



Priority:



Medium



\---



\## TD-006



DeviceSelector



目前仅演示。



未来接入：



\- Backup

\- Restore

\- Cloud

\- Operation



Priority:



High



\---



\# Current Priority



1\. Resource Registry



2\. Operation Engine



3\. Task Engine



4\. Monitoring



5\. Backup Integration



6\. Remote



7\. Automation



8\. AI Assistant



\---



\# Current Version Roadmap



v0.2.0



Foundation



✅



v0.3.0



Device Registry



✅



v0.4.0



Resource Registry



⏳



v0.5.0



Operation Engine



⬜



v0.6.0



Task Engine



⬜



v0.7.0



Monitoring



⬜



v0.8.0



Backup Integration



⬜



v0.9.0



Remote



⬜



v1.0.0



First Stable Release



\---



\# Do Not Touch



未经批准不得修改：



\- AI\_GUARD.md

\- 00\_PROJECT\_CHARTER.md

\- 03\_ARCHITECTURE.md

\- 05\_DATA\_MODEL.md



如需修改：



必须先进行 Architecture Review。



\---



\# Notes



PROJECT\_STATE.md 是整个 WorkOps 项目的唯一状态文件。



每完成一个 Sprint：



必须更新：



\- Version

\- Current Sprint

\- Completed

\- Review Status

\- Technical Debt

\- Current Priority

