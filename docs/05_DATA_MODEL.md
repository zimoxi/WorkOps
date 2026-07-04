# Data Model

Version: 1.0

Status: Active

---

# Device Table

```sql
CREATE TABLE IF NOT EXISTS device (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    type        TEXT NOT NULL,
    ip          TEXT DEFAULT '',
    status      TEXT DEFAULT 'offline',
    description TEXT DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
```

## Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| id | TEXT | Yes | - | UUID, 主键 |
| name | TEXT | Yes | - | 设备名称 |
| type | TEXT | Yes | - | 设备类型 |
| ip | TEXT | No | '' | IP 地址 |
| status | TEXT | No | 'offline' | 状态 |
| description | TEXT | No | '' | 描述 |
| created_at | TEXT | Yes | - | 创建时间 ISO8601 |
| updated_at | TEXT | Yes | - | 更新时间 ISO8601 |

## Device Types

- `windows` - Windows PC
- `linux` - Linux Server
- `omv` - OpenMediaVault
- `pve` - Proxmox VE
- `pbs` - Proxmox Backup Server
- `nas` - NAS
- `router` - Router
- `other` - 其他

## Device Status

- `online` - 在线
- `offline` - 离线
- `unknown` - 未知

---

# Future Tables

以下表格将在后续 Sprint 中添加：

- `service` - 设备服务能力
- `resource` - 设备资源
- `operation` - 操作
- `task` - 任务执行记录
- `monitor` - 监控数据

所有表格必须包含 `device_id` 外键。
