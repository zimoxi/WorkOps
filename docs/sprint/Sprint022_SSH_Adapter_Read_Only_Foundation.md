# Sprint022 — SSH Adapter Read-Only Foundation

Version: 1.0

Status: Ready

---

# Objective

建立受控的 SSH Adapter Read-Only Foundation。

本 Sprint 仅允许：

- SSH 连接能力基础
- 主机密钥验证
- 连接超时
- 只读状态查询
- 固定白名单查询
- 安全连接清理
- Mock 与 SSH Adapter 共存
- 受控实验环境验证

本 Sprint 不允许任意远程命令执行。

---

# Core Execution Boundary

调用链必须保持：

```
Task
    ↓
ExecutionService
    ↓
AdapterFactory
    ↓
SSHAdapter
    ↓
ReadOnlyQuery
```

禁止：

- Operation → SSHAdapter
- Scheduler → SSHAdapter
- API → SSHAdapter

Task 仍然是唯一执行入口。

但本 Sprint 不新增 Task 执行 API，也不自动触发 SSH 查询。

---

# 允许的能力

1. SSHAdapter 实现 connect()
2. SSHAdapter 实现 disconnect()
3. SSHAdapter 实现 query_status()
4. SSHAdapter 实现受限 read-only query
5. 主机密钥校验
6. known_hosts 路径配置
7. 连接超时
8. 命令超时
9. 安全异常映射
10. 输出长度限制
11. 输出脱敏
12. 受控测试设备手动验证

---

# 禁止任意命令

禁止提供：

```
execute(command_from_user)
```

禁止接收：

- 任意 shell 命令
- 用户提交的 command 字符串
- 前端提交的 command
- API 请求中的 command
- Task 中任意 command 字段
- 配置文件中的自定义 shell 命令

SSHAdapter 不得成为通用远程终端。

---

# 只读查询白名单

必须使用固定 Query ID，而不是命令字符串。

建议：

```
system.identity
system.uptime
system.os
system.hostname
system.disk_summary
system.memory_summary
```

调用形式：

```python
query_status(query_id)
```

或：

```python
execute_readonly(query_id)
```

内部由固定模板映射到命令。

禁止调用方直接提供命令。

---

# 白名单命令要求

每个 Query ID 必须对应：

- 固定命令
- 固定参数
- 无 shell 拼接
- 无用户输入插值
- 无路径输入
- 无环境变量输入
- 无管道
- 无重定向
- 无命令替换
- 无 sudo
- 无写文件
- 无服务重启
- 无安装软件
- 无权限修改

禁止使用：

- shell=True
- eval
- exec
- subprocess
- PowerShell
- 动态字符串拼接

---

# 只读命令审查

每个命令必须确认：

- 不修改系统状态
- 不写入文件
- 不修改时间戳
- 不触发更新
- 不读取敏感文件
- 不输出密码或私钥
- 不读取 shell history
- 不读取环境变量全集
- 不读取用户家目录敏感内容

不得使用：

```
cat /etc/shadow
cat ~/.ssh/*
env
printenv
history
ps e
/proc/*/environ
```

---

# 主机密钥验证

默认必须严格验证 SSH Host Key。

允许策略：

- STRICT
- TOFU_PENDING

禁止：

- AUTO_ACCEPT
- IGNORE
- DISABLED

## STRICT

- 主机密钥必须已经存在于受控 known_hosts
- 不匹配时立即拒绝
- 不自动覆盖旧密钥

## TOFU_PENDING

- 只允许在受控实验环境使用
- 首次发现密钥只返回 fingerprint
- 不自动写入 known_hosts
- 必须由管理员显式确认后才能信任

禁止默认：

- AutoAddPolicy
- WarningPolicy
- 跳过 Host Key 验证

---

# Fingerprint

Fingerprint 输出只允许：

- 算法
- SHA-256 Fingerprint
- 主机标识

不得输出：

- 私钥
- 完整凭据
- Secret Value
- known_hosts 全文件内容

---

# Credential 边界

SSHAdapter 只能通过 SecretProvider 获取 Secret。

调用链：

```
credential metadata
    ↓
secret_ref
    ↓
SecretProvider.retrieve()
    ↓
SecretValue
    ↓
显式 reveal()
    ↓
SSH 客户端连接
```

禁止：

- 密码写入 Device Model
- 密码写入 Task
- 密码写入日志
- 密码写入异常
- 密码写入配置文件
- 密码写入 API Response
- 密码写入 jobs.jsonl
- 在 Adapter 中长期缓存 Secret

连接尝试结束后：

- 删除局部 Secret 引用
- 不打印 Secret
- 不宣称 Python 内存已安全清零

---

# 支持的认证方式

本 Sprint 建议只允许一种认证方式。

优先裁决：

- password

或：

- private_key

不得同时一次实现所有方式。

Architecture Review 必须根据现有依赖和测试条件选择。

禁止：

- keyboard-interactive
- SSH Agent 自动遍历
- 密钥目录自动扫描
- 自动尝试所有本地私钥
- 空密码降级
- 不安全认证回退

---

# 依赖要求

Architecture Review 前不得安装 SSH 库。

必须先扫描：

- 当前 executor.py SSH 实现
- 是否已有 paramiko
- 是否使用系统 ssh.exe
- Windows/Linux 兼容性
- 依赖许可证
- 中国镜像可用性
- Host Key 支持能力
- 超时和取消支持能力

不得默认选用库。

---

# 连接配置

只允许：

- host
- port
- username
- credential_id
- host_key_policy
- known_hosts_path
- connect_timeout
- command_timeout

禁止：

- password
- private_key 原文
- token
- 任意 command
- shell 参数
- sudo 密码
- 完整连接字符串

---

# 网络边界

Sprint022 只允许连接明确配置的单个测试主机。

禁止：

- 网络扫描
- 子网扫描
- 端口扫描
- 自动发现 SSH 主机
- 批量连接
- CIDR 输入
- 广播探测
- 横向移动
- 跳板机
- ProxyCommand
- SSH Tunnel
- 端口转发

---

# 输出边界

SSH 查询结果必须：

- 限制最大 stdout 长度
- 限制最大 stderr 长度
- 使用 Redaction Utility
- 不返回原始异常全文
- 不返回连接配置原文
- 不返回 Secret
- 不返回完整 known_hosts
- 不返回客户端内部对象

输出过长时：

- 安全截断
- 标记 truncated=true
- 不把完整输出写入日志

---

# 错误模型

建议定义：

```
SSHAdapterError
SSHConfigurationError
SSHAuthenticationError
SSHHostKeyError
SSHConnectionError
SSHTimeoutError
SSHQueryNotAllowedError
SSHQueryExecutionError
```

要求：

- 错误消息不包含密码
- 不包含私钥
- 不包含完整 secret_ref
- 不包含完整连接字符串
- 不包含底层异常全文
- 可以包含安全错误代码
- 可以包含 host 和 port，但需评估日志暴露范围

---

# Mock 与 SSH 共存

AdapterFactory 必须继续支持：

```
mock
```

新增：

```
ssh_readonly
```

不得将现有：

```
ssh
```

占位类型直接变成可执行任意命令的 Adapter。

建议使用明确名称：

```
ssh_readonly
```

避免未来误认为支持通用 SSH 执行。

---

# 真实测试分级

## 规格和 Coding 阶段

- 不连接真实设备

## 单元测试

- 使用 Fake SSH Client
- 不访问网络

## Architecture Review 和代码 Review 通过后

允许在受控实验主机进行一次手动验证。

实验主机必须：

- 用户明确拥有或获授权
- 使用低权限账户
- 不属于生产环境
- 不包含敏感数据
- 不允许 sudo
- 不允许写操作
- 可以随时重建
- 网络范围明确

---

# 禁止

- 任意命令执行
- 通用 Shell API
- Backup
- Restore
- 文件上传
- 文件下载
- SCP
- SFTP
- SSH Tunnel
- 端口转发
- sudo
- root 登录
- WinRM
- SNMP
- PVE
- NAS
- Cloud
- Scheduler 自动触发
- Execution API
- 修改前端
- 修改权限矩阵
- 网络扫描
- 批量设备连接
- 生产设备连接

---

# Test Requirements

必须包含：

- SSHAdapter 不接受任意 command
- 只接受批准的 Query ID
- 未知 Query ID 被拒绝
- 白名单命令无用户输入插值
- 严格 Host Key 验证
- Host Key 不匹配拒绝
- TOFU 不自动信任
- 认证失败安全异常
- 连接失败安全异常
- 连接超时
- 查询超时
- finally 断开连接
- Secret 不进入日志
- Secret 不进入异常
- secret_ref 不完整暴露
- stdout/stderr Redaction
- 输出长度限制
- 超长输出安全截断
- Fake SSH Client 单元测试
- 单元测试不访问网络
- 不使用 subprocess
- 不使用系统 shell
- 不支持 SFTP/SCP/Tunnel
- 不支持 root/sudo
- 不支持批量扫描
- Sprint021 Credentials 测试继续通过
- Sprint020 Persistence 测试继续通过
- 原有 251 项测试继续通过
- 新增测试全部通过
- Full Suite 连续运行两次

---

# 完成标准

1. SSH Read-Only Adapter 架构建立。
2. 不存在任意命令入口。
3. 主机密钥严格验证。
4. 凭据仅通过 SecretProvider 获取。
5. 单元测试不访问真实网络。
6. 不连接生产设备。
7. 不实现 Backup/Restore。
8. 不实现 API 或前端按钮。
9. Full Suite 全部通过。
10. Architecture Review 通过前不安装依赖。
