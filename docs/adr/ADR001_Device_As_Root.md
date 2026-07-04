\# ADR001 - Device As Root Entity



Status: Accepted



Date: 2026-07-03



\---



\# Context



WorkOps 需要统一管理：



\- Windows

\- Linux

\- NAS

\- PVE

\- PBS

\- Docker

\- Cloud



如果每个模块拥有自己的资源体系，系统将变得复杂且难以扩展。



因此需要确定唯一根实体。



\---



\# Decision



Device 被定义为整个 WorkOps 唯一根实体（Root Entity）。



所有对象都必须关联到 Device。



包括：



\- Resource

\- Capability

\- Operation

\- Task

\- Monitoring

\- Notification



\---



\# Consequences



优点：



\- 数据关系清晰

\- 导航统一

\- API 一致

\- 易于扩展

\- AI 易于分析



限制：



所有新功能必须建立 Device 关联。



如果某功能无法关联 Device，则必须重新评估设计。



\---



\# Example



Windows-PC



├── Resources



├── Operations



├── Tasks



├── Monitoring



├── Remote



└── AI Insight



PVE



├── Resources



├── Operations



├── Tasks



├── Monitoring



└── AI Insight



所有对象最终都可以追溯到 Device。



\---



\# Decision Owner



Chief Architect



\---



\# Status



Accepted

