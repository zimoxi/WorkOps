# Sprint019 — Alpha Stabilization and Test Debt

Version: 1.0

Status: Ready

---

# Objective

稳定 WorkOps v0.6.0-alpha 测试基线。

处理 M3 Final Review 中记录的既有测试债：

- 15 个 HTTP API 测试失败
- 1 个 Frontend 测试失败

本 Sprint 目标是：

1. 找出每个失败测试的真实原因
2. 区分代码缺陷、测试过时和环境问题
3. 以最小修改修复
4. 建立可信的完整测试基线
5. 为 M4 后续 Persistence 和 Credential Sprint 提供稳定基础

---

# 允许

- 修复过时测试
- 修复测试发现的现有代码缺陷
- 修复 Windows 文件锁定问题
- 修复 HTTP API 测试启动、端口、Cookie、Session 或响应格式问题
- 修复 Frontend 测试选择器、加载顺序或 i18n 测试问题
- 增加测试辅助工具
- 增加测试隔离
- 增加临时目录和清理机制
- 更新测试文档
- 更新测试基线报告

---

# 禁止

- 连接真实设备
- 真实 SSH
- 真实 WinRM
- 真实 SNMP
- 真实命令执行
- 新增业务功能
- 新增 API 能力
- 新增执行 API
- 数据库
- ORM
- Persistence 实现
- Credential 实现
- 修改权限矩阵
- 修改 Data Model
- 大规模重构 server.py
- 修改 M2/M3 Architecture

---

# 失败分类

每个失败测试必须归类为：

| 分类 | 说明 |
|------|------|
| CODE_DEFECT | 当前代码确有缺陷 |
| OUTDATED_TEST | 测试断言与当前已批准架构不一致 |
| ENVIRONMENT_ISSUE | Windows 文件锁、端口占用、路径或运行环境问题 |
| TEST_ISOLATION | 测试之间共享状态、Cookie、Session、文件或进程 |
| UNKNOWN | 暂未确定，必须继续调查，不得猜测 |

---

# HTTP API 测试要求

调查 15 个失败测试：

- 测试服务是否正确启动和关闭
- 端口是否冲突
- Cookie 和 Session 是否隔离
- /api 与 /api/v1 路由是否混淆
- Response Format 是否与 Sprint014 一致
- Permission Middleware 是否影响测试
- Anonymous Viewer 策略是否导致断言过时
- 临时文件是否被 Windows 锁定
- 测试是否依赖执行顺序

不得通过删除测试或跳过测试来伪造通过。

---

# Frontend 测试要求

调查 1 个失败测试：

- DOM selector 是否过时
- script 加载顺序是否变化
- AuthModule 是否改变初始化流程
- Components、Store 或 i18n 是否未初始化
- 测试环境是否缺少浏览器能力

不得删除测试。

---

# 测试基线

完成后必须输出：

1. Sprint013—018 测试结果
2. M2 Core 测试结果
3. HTTP API 测试结果
4. Frontend 测试结果
5. 全量测试结果

必须明确：

- 测试总数
- 通过数
- 失败数
- 跳过数
- 每个失败的原因

---

# 兼容要求

保持兼容：

- M2 Core Engine
- Authentication
- API Layer
- Permission
- Repository
- Adapter
- Execution Engine

不得破坏：

- Git Tag M3-v0.6.0-alpha
- Git Tag M4-v0.7.0-architecture

---

# 完成标准

优先目标：

所有已知 16 个既有失败全部解决。

如果仍有失败：

- 必须有可复现步骤
- 必须有真实根因
- 必须说明是否阻塞 Sprint020
- 不得把失败描述为 pre-existing 后直接忽略

---

# Output

完成后停止并输出：

1. 文件路径
2. 文件是否创建成功
3. Sprint019 范围摘要
4. 是否准备输出 Sprint019 Implementation Plan
