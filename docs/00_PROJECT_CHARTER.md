\# WorkOps Project Charter



Version: 1.0



Status: Active



\---



\# 1. Mission（使命）



WorkOps 是一个统一管理个人、家庭实验室（HomeLab）和小型办公环境（SOHO）基础设施的平台。



WorkOps 的目标不是提供最多的功能，而是提供最好的管理体验。



一句话：



One Workspace. Every Infrastructure.



\---



\# 2. Product Vision（产品愿景）



用户只需要打开一个网页，就可以管理：



\- Windows

\- Linux

\- NAS

\- OMV

\- PVE

\- PBS

\- Docker

\- Cloud

\- Backup

\- Remote Access

\- Monitoring



无需切换多个系统。



\---



\# 3. Product Principles（产品原则）



\## Security First



安全优先。



默认不开放公网服务。



所有远程连接优先使用 Tailscale。



任何危险操作必须确认。



\---



\## Device First



所有资源必须属于某个 Device。



禁止脱离 Device 设计功能。



\---



\## Operation First



所有业务都是 Operation。



例如：



Backup



Restore



Migration



Snapshot



Cloud Sync



都属于 Operation。



\---



\## Mobile First



所有页面必须支持移动端。



手机是一级平台，不是附属平台。



\---



\## Local First



默认支持本地部署。



允许离线使用。



\---



\## AI Assisted



AI 是平台能力。



不是聊天工具。



AI 负责：



建议



分析



解释



辅助



不是自动执行。



\---



\# 4. What WorkOps Is



WorkOps 是：



统一基础设施管理平台。



不是：



Backup 软件。



不是：



NAS 管理器。



不是：



PVE 替代品。



不是：



Docker 面板。



\---



\# 5. What WorkOps Will Never Become



不会：



聊天软件



下载器



播放器



Office



浏览器



CMS



ERP



CRM



\---



\# 6. Architecture Rules



整个系统只有一个中心：



Device。



任何资源：



Storage



Backup



Remote



Cloud



Monitor



Task



必须关联 Device。



\---



\# 7. Development Rules



任何开发：



必须：



Architecture



↓



Sprint



↓



Implementation



↓



Review



↓



Release



禁止直接开发。



\---



\# 8. Documentation Rules



文档是真相。



代码是实现。



任何设计先更新文档，再开发。



\---



\# 9. AI Governance



ChatGPT



负责：



Architecture



Product



Database



API



Review



Roadmap



Hermes



负责：



Implementation



不得修改产品方向。



不得修改架构。



不得修改 Sprint 范围。



User



负责：



需求



验收



优先级



\---



\# 10. Success Criteria



如果未来：



用户能够：



打开 WorkOps。



看到：



所有设备。



所有资源。



所有任务。



所有备份。



所有监控。



所有远程入口。



则认为：



WorkOps 成功。

