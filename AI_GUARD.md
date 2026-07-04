\# WorkOps AI Guard



Version: 1.0



Status: Active



\---



\# Purpose



本文件定义所有 AI 开发助手（Hermes、Codex、ChatGPT、Claude、Gemini 等）的行为规范。



所有 AI 在执行任何开发任务前，必须先阅读本文件。



如果本文件与 Sprint 冲突，以本文件为准。



如果本文件与 Project Charter 冲突，以 Project Charter 为准。



\---



\# AI Responsibilities



AI 的职责：



\- 阅读文档

\- 实现 Sprint

\- 修复 Bug

\- 更新文档

\- 输出开发结果



AI 不负责：



\- 修改产品方向

\- 修改系统架构

\- 修改数据库模型

\- 修改一级导航

\- 自行增加功能



\---



\# Architecture Authority



只有以下文档可以定义架构：



\- docs/00\_PROJECT\_CHARTER.md

\- docs/03\_ARCHITECTURE.md

\- docs/05\_DATA\_MODEL.md

\- docs/adr/\*



AI 不得自行修改。



如需修改，必须停止并输出：



Architecture Decision Required



\---



\# Database Authority



AI 不得：



\- 新增核心数据表

\- 删除核心数据表

\- 新增核心字段

\- 修改字段含义



除非 Sprint 明确要求。



\---



\# Navigation Authority



一级导航固定：



\- 工作台

\- 设备

\- 资源

\- 操作

\- 任务

\- 监控

\- 远程

\- AI

\- 设置



AI 不得新增一级菜单。



\---



\# Sprint Authority



AI 只能完成当前 Sprint。



不得：



\- 提前开发

\- 顺便优化

\- 顺便重构

\- 顺便增加功能



完成当前 Sprint 后立即停止。



\---



\# Mock First



Foundation Sprint：



全部使用 Mock。



不得连接：



\- SSH

\- WinRM

\- SNMP

\- Docker

\- PVE

\- PBS

\- Restic

\- Rclone



\---



\# Safety



禁止自动执行：



\- 删除

\- 恢复

\- 覆盖

\- Backup

\- Restore

\- Snapshot

\- Migration

\- SSH



只能生成代码。



不得真正执行。



\---



\# Small Diff Principle



每次修改：



尽量影响最少文件。



禁止因为一个小需求重写整个项目。



优先：



Module Patch。



不是：



Rewrite。



\---



\# Coding



允许：



\- 新增模块

\- 新增组件

\- 新增测试

\- 修复 Bug



禁止：



\- 大规模重构

\- 修改架构

\- 修改领域模型



\---



\# Output



完成 Sprint 后只输出：



1\. 修改文件列表

2\. 新增文件列表

3\. API 变化

4\. 数据库变化

5\. 用户测试项



完成后停止。



不得进入下一 Sprint。



\---



\# Stop Rule



如果发现需要：



\- 修改 Architecture

\- 修改 Data Model

\- 修改 Domain

\- 修改导航

\- 修改数据库



必须立即停止。



输出：



Architecture Decision Required

