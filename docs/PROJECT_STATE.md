\# WorkOps Project State



Version: 0.2.0



Status: Active Development



Last Updated: 2026-07-04



\---



\# Current Stage



Current Phase: Foundation



Current Sprint: Sprint003 - Device Registry Foundation



Current Status: Planning



\---



\# Architecture



Architecture Status: Frozen



Current Architecture Version: 1.1



Current Data Model Version: 1.0



Core Domains:



\- Device

\- Resource

\- Operation

\- Task

\- Monitor



Device 是唯一 Root Entity。



禁止修改 Architecture。



禁止修改 Data Model。



如确需修改：



Architecture Decision Required



\---



\# Completed



✅ Project Charter



✅ Product Backlog



✅ Architecture



✅ Data Model



✅ AI Guard



✅ Sprint001 (Branding + i18n)



✅ Sprint002 (Workspace Foundation)



\---



\# Current Sprint



Sprint003



目标：



建立 Device Registry。



包含：



\- Device Registry 页面

\- Device Selector

\- Status Badge

\- Mock Device Store



全部使用 Mock。



不得连接真实设备。



\---



\# Next Sprint



Sprint004



Resource Registry Foundation



\---



\# Technical Debt



TD-001



server.py



INDEX\_HTML 仍然较大。



建议：



后续拆分模板。



Priority: Medium



\---



TD-002



static/app.js



文件仍然较大。



建议：



逐 Sprint 拆分模块。



Priority: High



\---



TD-003



Mock Data



目前写死在前端。



未来迁移至统一 Device Store。



Priority: Low



\---



\# Existing Modules



必须保持兼容：



\- Backup

\- Restore

\- NAS

\- Windows

\- Cloud

\- PVE

\- Jobs



不得破坏。



不得删除。



不得重构。



\---



\# Coding Rules



遵循：



AI\_GUARD.md



必须：



\- Small Diff

\- Mock First

\- Backward Compatible



禁止：



\- Rewrite

\- Large Refactor

\- Cross Sprint Development



\---



\# Before Coding



AI 必须：



1\. 阅读 AI\_GUARD.md

2\. 阅读 PROJECT\_STATE.md

3\. 阅读当前 Sprint

4\. 输出 Implementation Plan

5\. 等待确认



不得直接开始 Coding。



\---



\# Review Status



Sprint001: PASS



Sprint002: PASS



Sprint003: Planning



\---



\# Current Priority



1\. Device Registry

2\. Resource Registry

3\. Operation Engine

4\. Task Engine

5\. Monitoring

