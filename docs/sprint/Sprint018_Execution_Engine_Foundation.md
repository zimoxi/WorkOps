# Sprint018 — Execution Engine Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps Execution Engine 基础。

打通仅使用 MockAdapter 的执行链：

```
Task
    ↓
ExecutionService
    ↓
AdapterFactory
    ↓
MockAdapter
    ↓
Execution Result
```

本 Sprint 只验证执行架构，不连接真实设备。

---

# Core Principles

Task 是唯一执行入口。

禁止 Operation 直接调用 Adapter。

禁止 Scheduler 自动执行 Task。

ExecutionService 负责统一编排执行生命周期。

---

# Goals

- ExecutionService
- ExecutionContext
- ExecutionResult
- Mock Task Execution
- Task 状态生命周期
- 执行异常映射
- 内存状态更新
- 单元测试

---

# Task Lifecycle

只允许：

```
pending
    ↓
running
    ↓
success / failed / cancelled
```

禁止其他状态。

---

# ExecutionService Responsibilities

1. 根据 task_id 读取 Task
2. 验证 Task 当前状态
3. 将 Task 标记为 running
4. 创建 MockAdapter
5. 调用 connect()
6. 调用 execute()
7. 在 finally 中调用 disconnect()
8. 生成 ExecutionResult
9. 根据结果将 Task 更新为 success 或 failed
10. 返回统一执行结果

所有修改仅存在于内存 Mock 数据中。

不得持久化数据库。

---

# Error Handling

至少处理：

- TaskNotFoundError
- InvalidTaskStateError
- AdapterNotConnectedError
- AdapterExecutionError
- AdapterNotImplementedError
- ExecutionError

异常发生时：

- 尽量执行 disconnect()
- Task 状态更新为 failed
- 返回失败 ExecutionResult
- 不泄漏密码、连接参数或敏感信息

---

# ExecutionResult Fields

仅允许：

- task_id
- status
- started_at
- finished_at
- duration
- stdout
- stderr
- exit_code
- message

不得新增字段。

---

# 禁止

- 真实 SSH
- 真实 WinRM
- 真实 SNMP
- paramiko
- winrm
- pywinrm
- pysnmp
- socket 真实连接
- subprocess
- PowerShell
- Cron
- Timer
- 后台线程
- 数据库
- ORM
- 真正 Backup
- 真正 Restore
- Scheduler 自动触发
- Operation 直接执行
- 修改前端
- 新增执行按钮
- 新增 POST 执行 API
- 修改权限矩阵

---

# Compatibility

保持以下模块兼容：

- M2 所有模块
- Authentication
- API Layer
- Permission Foundation
- Repository Layer
- Device Adapter Foundation

不得修改任何 static/*.js 文件。

---

# Test Requirements

必须包含：

- Task 不存在
- 非 pending Task 拒绝执行
- pending → running → success
- MockAdapter connect
- MockAdapter execute
- finally disconnect
- Adapter 执行失败
- Task 最终变为 failed
- ExecutionResult 字段检查
- 禁止真实连接库检查
- Operation 不能直接调用 Adapter
- Scheduler 不自动触发执行

---

# Output

完成后输出：

1. 修改文件
2. 新增文件
3. 测试结果
4. 用户测试项
5. 已知限制
6. Technical Debt

完成后立即停止。
