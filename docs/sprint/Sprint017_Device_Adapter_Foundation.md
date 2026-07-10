# Sprint017 — Device Adapter Foundation

Version: 1.0

Status: Ready

---

# Objective

建立 Device Adapter 抽象层。

---

# Architecture

```
Task
    ↓
Service
    ↓
DeviceAdapter
    ↓
MockAdapter
```

---

# Adapter Interface

```python
class BaseAdapter(ABC):
    @abstractmethod
    def connect(self, device) -> bool:
        """连接设备"""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    def execute(self, command: str) -> dict:
        """执行命令"""
        pass

    @abstractmethod
    def query_status(self) -> dict:
        """查询设备状态"""
        pass
```

---

# Adapter Types

| Adapter | 说明 | 状态 |
|---------|------|------|
| BaseAdapter | 抽象接口 | 定义 |
| MockAdapter | Mock 实现 | 实现 |
| SSHAdapter | SSH 连接 | 空实现 |
| WinRMAdapter | WinRM 连接 | 空实现 |
| SNMPAdapter | SNMP 连接 | 空实现 |

---

# MockAdapter

实现 BaseAdapter：

- connect() → 返回 True
- disconnect() → 无操作
- execute() → 返回 Mock 结果
- query_status() → 返回 Mock 状态

---

# 禁止

- 真实连接
- 真实执行
- Task 执行
- 数据库
- 修改前端

---

# 测试要求

- Interface test：验证 BaseAdapter 接口定义
- MockAdapter test：验证 MockAdapter 实现

---

# Technical Debt

- TD-045: SSHAdapter 尚未实现真实 SSH 连接
- TD-046: WinRMAdapter 尚未实现真实 WinRM 连接
- TD-047: SNMPAdapter 尚未实现真实 SNMP 查询
- TD-048: AdapterFactory 暂不支持动态注册

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
