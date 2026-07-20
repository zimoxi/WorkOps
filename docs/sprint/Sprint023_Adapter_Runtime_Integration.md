# Sprint023 — Adapter Runtime Integration Foundation

## 1. Objective

建立统一 Adapter Runtime 层，为未来多 Adapter 扩展提供生命周期、能力声明、注册机制。

本 Sprint 只实现 Adapter Runtime 骨架，不增加任何执行能力。

## 2. Core Principles

- **Runtime 禁止保存 secret**：password, SecretValue, secret_ref, CredentialMetadata, private_key, token
- **Session 只能保存**：session_id, adapter_type, device_id, state, timestamps
- **所有模型不可变**：Descriptor, QueryResult, Capability 使用 frozen dataclass 或 Enum
- **不允许动态 import**：Registry 不使用 `__import__` 或 `import_module`
- **不允许用户输入控制 class 加载**：Registry 只接受已注册的类型
- **不跨 Sprint**：严格限制在当前 Sprint 范围内

## 3. Scope

### Implement

| File | Purpose |
|------|---------|
| `backup_manager/adapters/capabilities.py` | AdapterCapability Enum |
| `backup_manager/adapters/descriptor.py` | AdapterDescriptor frozen dataclass |
| `backup_manager/adapters/registry.py` | AdapterRegistry |
| `backup_manager/adapters/session.py` | AdapterSession 状态机 |
| `backup_manager/adapters/runtime.py` | AdapterRuntime 生命周期管理 |
| `backup_manager/adapters/result.py` | AdapterQueryResult 统一结果 |
| `backup_manager/adapters/errors.py` | 新增 Runtime 错误类 |
| `tests/test_adapter_runtime.py` | 测试 |

### Allowed Modifications

| File | Purpose |
|------|---------|
| `backup_manager/adapters/__init__.py` | 导出新模块 |
| `backup_manager/adapters/factory.py` | 新增 register_to_registry() |
| `backup_manager/adapters/mock_adapter.py` | 新增 query() 方法 |

## 4. Capability Model

```python
class AdapterCapability(Enum):
    STATUS_QUERY = "status_query"
    SYSTEM_QUERY = "system_query"
```

禁止注册：
- EXECUTE
- UPLOAD
- DOWNLOAD
- BACKUP
- RESTORE

## 5. Descriptor Model

```python
@dataclass(frozen=True, slots=True)
class AdapterDescriptor:
    adapter_type: str
    capabilities: frozenset
    readonly: bool
```

验证：
- `adapter_type` 非空字符串
- `capabilities` 非空 frozenset，所有元素为 AdapterCapability
- `readonly` 必须为 True

## 6. Registry Design

```python
class AdapterRegistry:
    register(descriptor, adapter_class)
    get_descriptor(adapter_type) -> AdapterDescriptor
    create(adapter_type, **kwargs) -> BaseAdapter
    list_types() -> list[str]
    is_registered(adapter_type) -> bool
```

约束：
- `duplicate adapter_type` → AdapterDuplicateError
- `unknown adapter_type` → AdapterNotRegisteredError
- 不允许动态 import
- 不允许用户输入控制 class 加载

## 7. Runtime Lifecycle

```
create_session(adapter_type, device_id)
    ↓
connect(session_id, config, **kwargs)
    ↓
query(session_id, query_id) → AdapterQueryResult
    ↓
close(session_id)  # 幂等，释放 adapter
```

约束：
- `close()` 幂等：已关闭的会话不报错
- `close()` 释放 adapter：从 `_adapters` 中移除
- 异常不泄漏 secret/credential/connection string
- 状态转换必须校验合法性

## 8. Session Security Boundary

```python
class SessionState(Enum):
    CREATED = "created"
    CONNECTED = "connected"
    CLOSED = "closed"
```

允许的状态转换：
| From | To | Valid |
|------|----|-------|
| CREATED | CONNECTED | ✅ |
| CREATED | CLOSED | ✅ |
| CONNECTED | CLOSED | ✅ |
| CLOSED | CONNECTED | ❌ |
| CONNECTED | CREATED | ❌ |

Session 只能保存：
- session_id
- adapter_type
- device_id
- state
- timestamps (created_at, connected_at, closed_at)

Session 禁止保存：
- client / paramiko client
- socket / transport
- secret / password / token

## 9. Query Result Contract

```python
@dataclass(frozen=True, slots=True)
class AdapterQueryResult:
    query_id: str
    success: bool
    data: dict
    message: str
    timestamp: str
```

禁止包含的字段：
- command
- stdout（外层）
- stderr（外层）
- password
- secret_ref

`data` 字典可包含 stdout/stderr/exit_code 等查询结果。

## 10. SSH Integration

修改 `factory.py`，新增 `register_to_registry()` 方法：

```python
ssh_desc = AdapterDescriptor(
    adapter_type="ssh_readonly",
    capabilities=frozenset({
        AdapterCapability.STATUS_QUERY,
        AdapterCapability.SYSTEM_QUERY,
    }),
    readonly=True,
)
registry.register(ssh_desc, SSHReadOnlyAdapter)
```

不重构 `ssh_readonly_adapter.py`。

## 11. Mock Adapter

在 `mock_adapter.py` 中新增 `query()` 方法：

```python
def query(self, query_id: str):
    """返回 MockSSHReadOnlyQueryResult，用于 Runtime 集成测试。"""
```

能力：STATUS_QUERY
禁止：execute() 仍保留但不用于 Runtime

## 12. Forbidden Scope

禁止修改：
- `backup_manager/server.py`
- `backup_manager/executor.py`
- `backup_manager/jobs.py`
- `backup_manager/auth_service.py`
- `backup_manager/device_repository.py`
- `static/*.js`

禁止实现：
- SSH execute / command execution / shell / subprocess
- backup / restore / network scan / device discovery
- credential persistence
- Credential Repository / Secret Storage

## 13. Test Requirements

最低覆盖：
- Capability enum 值和冻结
- Descriptor 校验（空类型、空能力、readonly=False、无效能力）
- Registry register/duplicate reject/unknown reject/create
- Session create/transition/close idempotent
- Runtime create/connect/query/close/full lifecycle
- Security: repr 不泄漏、session 不包含 secret、error 不包含 secret、无动态 import

运行：
```
python -m unittest tests.test_adapter_runtime
python -m unittest discover -s tests
```

要求：
- Sprint 测试全部通过
- Full Suite 连续两次通过
- 0 failed, 0 errors

## 14. Completion Criteria

| Criteria | Status |
|----------|--------|
| capabilities.py 存在 | ✅ |
| descriptor.py 存在 | ✅ |
| registry.py 存在 | ✅ |
| session.py 存在 | ✅ |
| runtime.py 存在 | ✅ |
| result.py 存在 | ✅ |
| errors.py 已更新 | ✅ |
| mock_adapter.py 已更新 | ✅ |
| factory.py 已更新 | ✅ |
| __init__.py 已更新 | ✅ |
| tests/test_adapter_runtime.py 存在 | ✅ |
| Sprint 测试通过 | ✅ 51/51 |
| Full Suite 通过 | ✅ 392/392 |
| 禁止范围未修改 | ✅ |
| Git commit | ✅ 938f4a4 |
| Git tag | ✅ Sprint023-Adapter-Runtime-v0.7.5 |
