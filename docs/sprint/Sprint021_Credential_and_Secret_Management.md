# Sprint021 — Credential and Secret Management

Version: 1.0

Status: Ready

---

# Objective

建立 WorkOps Credential and Secret Management 基础，为后续 Sprint022 SSH Read-Only 提供安全凭据边界。

本 Sprint 禁止连接任何真实设备。

---

# Core Principles

1. 凭据不得进入 Git。

2. 凭据不得进入普通日志。

3. 凭据不得进入普通 API Response。

4. 不允许明文密码持久化。

5. Service、Repository、Adapter 不得直接管理加密密钥。

6. Secret Provider 与业务逻辑解耦。

7. Credential Metadata 与 Secret Value 分离。

8. Sprint021 不实现真实 SSH、WinRM、SNMP。

---

# 允许

- Credential Model
- Credential Metadata
- SecretProvider Interface
- InMemorySecretProvider
- EncryptedFileSecretProvider 设计或最小本地实现
- Secret Reference
- Secret Redaction
- 日志脱敏
- 配置脱敏
- 测试专用 Mock Secret
- 密钥来源边界
- 凭据生命周期设计
- 单元测试

---

# Credential Metadata

仅允许保存：

- credential_id
- name
- credential_type
- username
- secret_ref
- created_at
- updated_at
- disabled_at

credential_type 仅允许：

- password
- private_key
- token

禁止在 Metadata 中保存 Secret 原文。

---

# Secret Value

Secret Value 只能通过 SecretProvider 存取。

接口建议：

```
store(secret_value) -> secret_ref
retrieve(secret_ref) -> secret_value
delete(secret_ref)
exists(secret_ref) -> bool
```

禁止：

- list_all_secrets()
- 将所有 Secret 返回给调用方
- Secret 出现在 repr()
- Secret 出现在 str()
- Secret 出现在异常消息

---

# SecretProvider

设计：

```
SecretProvider Interface
├── InMemorySecretProvider
└── EncryptedFileSecretProvider
```

本 Sprint 默认只允许 InMemorySecretProvider 用于测试。

EncryptedFileSecretProvider 是否实际实现，必须由 Architecture Review 决定。

不得自行设计加密算法。

如果没有可靠的系统密钥来源，只能先定义接口和安全边界，不得伪造"安全加密"。

---

# 密钥来源

必须明确评估：

- Windows DPAPI
- Linux Secret Service / 文件权限
- 环境变量
- 外部 Secret Manager

禁止：

- 加密密钥硬编码在源码
- 加密密钥提交到 Git
- 密钥与密文存放在同一普通配置文件
- 使用固定默认密钥
- 自制加密算法

---

# Redaction

必须建立统一脱敏函数。

至少识别：

- password
- passwd
- secret
- token
- access_token
- refresh_token
- private_key
- authorization
- cookie
- session_id

输出替换为：

```
[REDACTED]
```

不得只依赖字段名大小写完全匹配。

---

# 日志和错误

禁止日志输出：

- Secret Value
- 密码
- 私钥
- Token
- Cookie
- Session ID
- Authorization Header
- 完整连接字符串

异常消息只能包含：

- credential_id
- credential_type
- 安全错误代码

不得包含 Secret 原文。

---

# Persistence 边界

Sprint020 的 Persistence 可以保存 Credential Metadata，但不得保存 Secret Value 原文。

是否在 Sprint021 创建 credentials 表，必须由 Architecture Review 决定。

禁止修改：

- sessions 表设计
- Task Data Model
- ExecutionResult Data Model

---

# API 边界

本 Sprint 不增加 Credential 管理 API。

不允许：

- GET Secret
- 返回密码
- 返回私钥
- 返回 Token
- 前端展示 Secret
- 新增真实连接 API

---

# 禁止

- 真实 SSH
- WinRM
- SNMP
- paramiko
- pywinrm
- pysnmp
- subprocess
- 真实命令
- Backup
- Restore
- Execution API
- 修改前端
- 修改权限矩阵
- Session Persistence
- 自制加密算法
- 明文 Secret 数据库字段

---

# Test Requirements

必须包含：

- Credential Metadata 不包含 Secret 原文
- InMemorySecretProvider store/retrieve/delete
- 不存在 secret_ref
- Secret 不出现在 repr/str
- Secret 不出现在异常消息
- Redaction 支持大小写变化
- Redaction 支持嵌套字典和列表
- 日志脱敏
- 配置脱敏
- 未知 credential_type 拒绝
- 空 Secret 拒绝
- SecretProvider 不支持 list_all
- 不引入真实连接库
- 不修改 static/*.js
- Sprint020 Persistence 测试继续通过
- Full Suite 连续通过两次

---

# Technical Debt

| ID | 说明 | 状态 |
|----|------|------|
| TD-057 | JobRecord 写入前接入 redact() | 待后续 Sprint |
| TD-058 | HTTP 错误响应统一安全异常映射 | 待后续 Sprint |
| TD-059 | 日志输出前统一 Redaction | 待后续 Sprint |
| TD-060 | 持久化 Secret Provider 与可靠系统密钥来源尚未确定，需要单独 Architecture Review；不得默认实现 EncryptedFileSecretProvider | 待 Architecture Review |
