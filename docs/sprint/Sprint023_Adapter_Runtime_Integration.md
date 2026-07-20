# Sprint023 — Adapter Runtime Integration Foundation

## Objective

建立统一 Adapter Runtime 层，为未来多 Adapter 扩展提供生命周期、能力声明、注册机制。

## Scope

只实现 Adapter Runtime 骨架，不增加任何执行能力。

## Deliverables

| File | Purpose |
|------|---------|
| `backup_manager/adapters/capabilities.py` | AdapterCapability Enum |
| `backup_manager/adapters/descriptor.py` | AdapterDescriptor frozen dataclass |
| `backup_manager/adapters/registry.py` | AdapterRegistry |
| `backup_manager/adapters/session.py` | AdapterSession 状态机 |
| `backup_manager/adapters/runtime.py` | AdapterRuntime 生命周期管理 |
| `backup_manager/adapters/result.py` | AdapterQueryResult 统一结果 |
| `backup_manager/adapters/errors.py` | 新增 Runtime 错误 |
| `tests/test_adapter_runtime.py` | 测试 |

## Frozen Scope

禁止：
- SSH execute / command execution / shell / subprocess
- backup / restore / network scan / device discovery
- credential persistence
- Credential Repository / Secret Storage
- 修改 server.py / executor.py / jobs.py / auth_service.py / device_repository.py / static/*.js

## Security Boundary

Runtime 禁止保存：password, SecretValue, secret_ref, CredentialMetadata, private_key, token

Session 只能保存：session_id, adapter_type, device_id, state, timestamps
