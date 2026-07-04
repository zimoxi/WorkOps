\# WorkOps Product Backlog



Version: 1.0



Status: Active



Last Updated: 2026-07-04



\---



\# Purpose



本文件定义 WorkOps 的长期开发路线。



所有 Sprint 必须来源于本 Backlog。



Hermes 不得自行新增 Epic 或修改优先级。



产品优先级由 Product Owner 决定。



\---



\# Development Principles



开发原则：



\- Workspace First

\- Device First

\- Mock First

\- Foundation Before Feature

\- Small Sprint

\- Backward Compatible



任何新功能必须先进入 Backlog，再进入 Sprint。



\---



\# Development Status



\## Completed



\- Project Charter

\- Architecture

\- Data Model

\- AI Guard

\- Branding

\- i18n

\- Workspace Foundation



\---



\# Epic WF - Workspace



目标：



建立统一工作台。



\## WF-001



Workspace Layout



Status:



Completed



\## WF-002



Workspace Widgets



Status:



Completed



\## WF-003



Responsive Layout



Status:



Completed



Future：



\- Workspace Customization

\- Dashboard Layout

\- User Widgets



\---



\# Epic DR - Device



目标：



建立统一 Device Registry。



\## DR-001



Device Registry



Status:



Planned



Priority:



High



\## DR-002



Device Selector



Status:



Planned



Priority:



High



\## DR-003



Device Identity



Status:



Planned



Priority:



Medium



\## DR-004



Device Detail



Status:



Future



\---



\# Epic RR - Resource



目标：



建立统一 Resource Registry。



包含：



\- Disk

\- Folder

\- Dataset

\- Share

\- VM

\- Container



Status:



Planned



\---



\# Epic OE - Operation



目标：



建立统一 Operation Engine。



包含：



\- Backup

\- Restore

\- Snapshot

\- Migration

\- Verify

\- Cloud Sync



Status:



Planned



\---



\# Epic TE - Task



目标：



统一 Task 生命周期。



包含：



\- Pending

\- Running

\- Success

\- Failed

\- Cancelled



Status:



Planned



\---



\# Epic MO - Monitoring



目标：



统一监控能力。



包含：



\- CPU

\- Memory

\- Disk

\- SMART

\- Network

\- Temperature



Status:



Planned



\---



\# Epic RM - Remote



目标：



统一远程访问。



包含：



\- SSH

\- RDP

\- SFTP

\- File Browser

\- Terminal



Status:



Future



\---



\# Epic BK - Backup



目标：



统一备份能力。



包含：



\- Restic

\- Windows Backup

\- Cloud Backup

\- Verify

\- Retention



Status:



Future



\---



\# Epic CL - Cloud



目标：



统一云端能力。



包含：



\- Rclone

\- OneDrive

\- Google Drive

\- S3

\- Backblaze B2



Status:



Future



\---



\# Epic PV - Virtualization



目标：



统一虚拟化管理。



包含：



\- PVE

\- PBS

\- LXC

\- VM



Status:



Future



\---



\# Epic CT - Containers



目标：



统一容器管理。



包含：



\- Docker

\- Docker Compose

\- Podman（预留）



Status:



Future



\---



\# Epic AI - AI Assistant



目标：



AI 辅助运维。



包含：



\- 日志分析

\- 告警分析

\- 配置建议

\- 故障定位

\- 自动生成命令



Status:



Future



\---



\# Epic AU - Automation



目标：



自动化执行。



包含：



\- Workflow

\- Scheduler

\- Trigger

\- Script

\- Pipeline



Status:



Future



\---



\# Epic NT - Notification



目标：



统一通知。



包含：



\- Email

\- Telegram

\- WeCom

\- Discord

\- Webhook



Status:



Future



\---



\# Epic RB - Security



目标：



权限与安全。



包含：



\- Multi User

\- RBAC

\- Audit Log

\- API Token

\- MFA（预留）



Status:



Future



\---



\# Sprint Rules



每个 Sprint：



\- 只允许对应一个 Epic

\- 时间控制在 1～2 天

\- 必须可运行

\- 必须可验收

\- 必须通过 Review



不得跨 Epic 同时开发。



\---



\# Priority



当前开发顺序：



1\. Device Registry

2\. Resource Registry

3\. Operation Engine

4\. Task Engine

5\. Monitoring

6\. Backup Integration

7\. Remote

8\. Cloud

9\. Virtualization

10\. AI Assistant



\---



\# Out of Scope (V1)



以下功能不属于 V1：



\- Kubernetes

\- Multi-node Cluster

\- High Availability

\- Multi-Tenant

\- Billing

\- Marketplace



\---



\# Change Policy



新增 Epic：



必须修改：



\- Project Charter（如涉及产品定位）

\- Architecture（如涉及领域模型）

\- Product Backlog



新增 Sprint：



必须来源于本 Backlog。



Hermes 不得自行新增 Sprint。



\---



\# Vision



WorkOps 的目标不是成为单一的备份软件。



WorkOps 是一个统一基础设施运维平台（Unified Infrastructure Operations Platform）。



用户可以通过一个 Web 控制台统一管理：



\- Windows

\- Linux

\- NAS

\- OMV

\- PVE

\- PBS

\- Docker

\- Backup

\- Restore

\- Remote

\- Monitoring

\- Automation

\- AI Assistant



所有能力共享统一的数据模型、统一的界面和统一的操作体验。

