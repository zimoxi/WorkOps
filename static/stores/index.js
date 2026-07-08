/**
 * WorkOps Unified Store — 统一数据源
 * Sprint010: Unified Store Foundation
 *
 * 所有 Mock 数据统一放在此文件中。
 * 通过 window.XxxStore 暴露给业务模块。
 *
 * Store API 最小化：
 * - getAll() — 返回数组副本
 * - getById(id) — 返回对象副本或 null
 *
 * 不提供：find / filter / update / delete / save
 * 所有过滤、排序、分组继续放在业务模块。
 */
(function () {
  "use strict";

  // ─── 工具函数 ────────────────────────────────────────
  function findById(data, id) {
    for (var i = 0; i < data.length; i++) {
      if (data[i].id === id) return Object.assign({}, data[i]);
    }
    return null;
  }

  // ─── Device Store ─────────────────────────────────────
  var deviceData = [
    { id: "550e8400-e29b-41d4-a716-446655440001", name: "Windows-PC", type: "windows", status: "online", ip: "192.168.1.100" },
    { id: "550e8400-e29b-41d4-a716-446655440002", name: "Linux-Server", type: "linux", status: "online", ip: "192.168.1.10" },
    { id: "550e8400-e29b-41d4-a716-446655440003", name: "NAS-01", type: "nas", status: "online", ip: "192.168.1.2" },
    { id: "550e8400-e29b-41d4-a716-446655440004", name: "OMV", type: "omv", status: "online", ip: "192.168.1.5" },
    { id: "550e8400-e29b-41d4-a716-446655440005", name: "PVE", type: "pve", status: "online", ip: "192.168.1.3" },
    { id: "550e8400-e29b-41d4-a716-446655440006", name: "PBS", type: "pbs", status: "offline", ip: "192.168.1.4" },
    { id: "550e8400-e29b-41d4-a716-446655440007", name: "Router", type: "router", status: "online", ip: "192.168.1.1" },
  ];

  window.DeviceStore = {
    getAll: function () { return deviceData.slice(); },
    getById: function (id) { return findById(deviceData, id); }
  };

  // ─── Resource Store ───────────────────────────────────
  var resourceData = [
    // Windows-PC 的资源
    { id: "r-001", device_id: "550e8400-e29b-41d4-a716-446655440001", device_name: "Windows-PC", name: "Disk C", type: "disk", path: "C:\\", mount_point: "C:\\", size_total: "512GB", size_used: "320GB", status: "online" },
    { id: "r-002", device_id: "550e8400-e29b-41d4-a716-446655440001", device_name: "Windows-PC", name: "Disk D", type: "disk", path: "D:\\", mount_point: "D:\\", size_total: "2TB", size_used: "1.2TB", status: "online" },
    { id: "r-003", device_id: "550e8400-e29b-41d4-a716-446655440001", device_name: "Windows-PC", name: "Backup Folder", type: "folder", path: "D:\\Backup", mount_point: "-", size_total: "-", size_used: "-", status: "online" },

    // NAS-01 的资源
    { id: "r-004", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", name: "Pool tank", type: "dataset", path: "tank", mount_point: "/mnt/tank", size_total: "16TB", size_used: "8.5TB", status: "online" },
    { id: "r-005", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", name: "Dataset photos", type: "dataset", path: "tank/photos", mount_point: "/mnt/tank/photos", size_total: "4TB", size_used: "2.1TB", status: "online" },
    { id: "r-006", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", name: "Share backup", type: "share", path: "/mnt/tank/backup", mount_point: "-", size_total: "8TB", size_used: "5.2TB", status: "online" },

    // PVE 的资源
    { id: "r-007", device_id: "550e8400-e29b-41d4-a716-446655440005", device_name: "PVE", name: "VM 101", type: "vm", path: "101", mount_point: "-", size_total: "100GB", size_used: "45GB", status: "online" },
    { id: "r-008", device_id: "550e8400-e29b-41d4-a716-446655440005", device_name: "PVE", name: "VM 102", type: "vm", path: "102", mount_point: "-", size_total: "200GB", size_used: "120GB", status: "online" },
    { id: "r-009", device_id: "550e8400-e29b-41d4-a716-446655440005", device_name: "PVE", name: "Storage local-lvm", type: "storage", path: "local-lvm", mount_point: "-", size_total: "500GB", size_used: "280GB", status: "online" },

    // OMV 的资源
    { id: "r-010", device_id: "550e8400-e29b-41d4-a716-446655440004", device_name: "OMV", name: "Share data", type: "share", path: "/sharedfolders/data", mount_point: "-", size_total: "4TB", size_used: "2.8TB", status: "online" },
    { id: "r-011", device_id: "550e8400-e29b-41d4-a716-446655440004", device_name: "OMV", name: "Share media", type: "share", path: "/sharedfolders/media", mount_point: "-", size_total: "8TB", size_used: "6.1TB", status: "online" },
  ];

  window.ResourceStore = {
    getAll: function () { return resourceData.slice(); },
    getById: function (id) { return findById(resourceData, id); }
  };

  // ─── Operation Store ──────────────────────────────────
  var operationData = [
    // Windows-PC 的操作
    { id: "op-001", name: "Daily Backup", type: "backup", device_id: "550e8400-e29b-41d4-a716-446655440001", device_name: "Windows-PC", resource_id: "r-001", resource_name: "Disk C", schedule: "daily", last_run: "2026-07-04 02:00", status: "success" },

    // NAS-01 的操作
    { id: "op-002", name: "NAS Photos Backup", type: "backup", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", resource_id: "r-005", resource_name: "Dataset photos", schedule: "weekly", last_run: "2026-07-01 03:00", status: "success" },
    { id: "op-003", name: "Daily Snapshot", type: "snapshot", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", resource_id: "r-004", resource_name: "Pool tank", schedule: "daily", last_run: "2026-07-04 01:00", status: "success" },
    { id: "op-004", name: "Backup Verify", type: "verify", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", resource_id: "r-006", resource_name: "Share backup", schedule: "weekly", last_run: "2026-07-03 04:00", status: "success" },
    { id: "op-005", name: "Cloud Sync", type: "cloud_sync", device_id: "550e8400-e29b-41d4-a716-446655440003", device_name: "NAS-01", resource_id: "r-006", resource_name: "Share backup", schedule: "daily", last_run: "2026-07-04 05:00", status: "success" },

    // Linux-Server 的操作
    { id: "op-006", name: "Test Restore", type: "restore", device_id: "550e8400-e29b-41d4-a716-446655440002", device_name: "Linux-Server", resource_id: "r-004", resource_name: "Pool tank", schedule: "manual", last_run: "2026-06-28 10:00", status: "success" },

    // PVE 的操作
    { id: "op-007", name: "Data Migration", type: "migration", device_id: "550e8400-e29b-41d4-a716-446655440005", device_name: "PVE", resource_id: "r-009", resource_name: "Storage local-lvm", schedule: "manual", last_run: "-", status: "pending" },
  ];

  window.OperationStore = {
    getAll: function () { return operationData.slice(); },
    getById: function (id) { return findById(operationData, id); }
  };

  // ─── Task Store ───────────────────────────────────────
  var taskData = [
    // Daily Backup (op-001) 的任务
    { id: "task-001", operation_id: "op-001", operation_name: "Daily Backup", device_name: "Windows-PC", resource_name: "Disk C", status: "success", start_time: "2026-07-04 02:00", end_time: "2026-07-04 02:05:30", duration: "5m30s", result: "备份完成，共 320GB" },
    { id: "task-002", operation_id: "op-001", operation_name: "Daily Backup", device_name: "Windows-PC", resource_name: "Disk C", status: "success", start_time: "2026-07-03 02:00", end_time: "2026-07-03 02:04:45", duration: "4m45s", result: "备份完成，共 318GB" },
    { id: "task-003", operation_id: "op-001", operation_name: "Daily Backup", device_name: "Windows-PC", resource_name: "Disk C", status: "failed", start_time: "2026-07-02 02:00", end_time: "2026-07-02 02:01:20", duration: "1m20s", result: "错误：连接超时" },

    // NAS Photos Backup (op-002) 的任务
    { id: "task-004", operation_id: "op-002", operation_name: "NAS Photos Backup", device_name: "NAS-01", resource_name: "Dataset photos", status: "success", start_time: "2026-07-01 03:00", end_time: "2026-07-01 03:15:00", duration: "15m00s", result: "备份完成，共 2.1TB" },

    // Daily Snapshot (op-003) 的任务
    { id: "task-005", operation_id: "op-003", operation_name: "Daily Snapshot", device_name: "NAS-01", resource_name: "Pool tank", status: "success", start_time: "2026-07-04 01:00", end_time: "2026-07-04 01:02:15", duration: "2m15s", result: "快照创建成功" },
    { id: "task-006", operation_id: "op-003", operation_name: "Daily Snapshot", device_name: "NAS-01", resource_name: "Pool tank", status: "success", start_time: "2026-07-03 01:00", end_time: "2026-07-03 01:02:30", duration: "2m30s", result: "快照创建成功" },

    // Cloud Sync (op-005) 的任务
    { id: "task-007", operation_id: "op-005", operation_name: "Cloud Sync", device_name: "NAS-01", resource_name: "Share backup", status: "success", start_time: "2026-07-04 05:00", end_time: "2026-07-04 05:10:00", duration: "10m00s", result: "同步完成，共 5.2TB" },
    { id: "task-008", operation_id: "op-005", operation_name: "Cloud Sync", device_name: "NAS-01", resource_name: "Share backup", status: "running", start_time: "2026-07-03 05:00", end_time: "-", duration: "-", result: "同步中..." },

    // Data Migration (op-007) 的任务
    { id: "task-009", operation_id: "op-007", operation_name: "Data Migration", device_name: "PVE", resource_name: "Storage local-lvm", status: "pending", start_time: "2026-07-04 10:00", end_time: "-", duration: "-", result: "等待执行" },
  ];

  window.TaskStore = {
    getAll: function () { return taskData.slice(); },
    getById: function (id) { return findById(taskData, id); }
  };

  // ─── Monitor Store ────────────────────────────────────
  var monitorData = [
    // Device Health
    { id: "mon-001", target_type: "device", target_name: "Windows-PC", status: "online", message: "设备正常运行", updated_at: "2026-07-04 12:00" },
    { id: "mon-002", target_type: "device", target_name: "Linux-Server", status: "online", message: "设备正常运行", updated_at: "2026-07-04 12:00" },
    { id: "mon-003", target_type: "device", target_name: "NAS-01", status: "online", message: "设备正常运行", updated_at: "2026-07-04 12:00" },
    { id: "mon-004", target_type: "device", target_name: "PVE", status: "warning", message: "CPU 使用率 78%", updated_at: "2026-07-04 12:00" },
    { id: "mon-005", target_type: "device", target_name: "PBS", status: "offline", message: "设备离线", updated_at: "2026-07-04 12:00" },

    // Resource Health
    { id: "mon-006", target_type: "resource", target_name: "Disk C", status: "online", message: "存储正常，已用 320/512GB", updated_at: "2026-07-04 12:00" },
    { id: "mon-007", target_type: "resource", target_name: "Pool tank", status: "online", message: "存储正常，已用 8.5/16TB", updated_at: "2026-07-04 12:00" },
    { id: "mon-008", target_type: "resource", target_name: "VM 101", status: "online", message: "虚拟机运行中，内存 45/100GB", updated_at: "2026-07-04 12:00" },

    // Operation Health
    { id: "mon-009", target_type: "operation", target_name: "Daily Backup", status: "success", message: "最近执行成功，耗时 5m30s", updated_at: "2026-07-04 02:05" },
    { id: "mon-010", target_type: "operation", target_name: "Cloud Sync", status: "running", message: "正在同步，已传输 3.2/5.2TB", updated_at: "2026-07-04 05:00" },

    // Task Health
    { id: "mon-011", target_type: "task", target_name: "task-001", status: "success", message: "任务执行成功，备份 320GB", updated_at: "2026-07-04 02:05" },
    { id: "mon-012", target_type: "task", target_name: "task-008", status: "running", message: "任务执行中，已运行 25 小时", updated_at: "2026-07-03 05:00" },
  ];

  window.MonitorStore = {
    getAll: function () { return monitorData.slice(); },
    getById: function (id) { return findById(monitorData, id); }
  };

  // ─── Schedule Store ───────────────────────────────────
  var scheduleData = [
    { id: "sch-001", operation_id: "op-001", operation_name: "Daily Backup", schedule_type: "daily", expression: "02:00", next_run: "2026-07-05 02:00", enabled: true },
    { id: "sch-002", operation_id: "op-002", operation_name: "NAS Photos Backup", schedule_type: "weekly", expression: "sunday 03:00", next_run: "2026-07-06 03:00", enabled: true },
    { id: "sch-003", operation_id: "op-003", operation_name: "Daily Snapshot", schedule_type: "daily", expression: "01:00", next_run: "2026-07-05 01:00", enabled: true },
    { id: "sch-004", operation_id: "op-004", operation_name: "Backup Verify", schedule_type: "weekly", expression: "saturday 04:00", next_run: "2026-07-05 04:00", enabled: true },
    { id: "sch-005", operation_id: "op-005", operation_name: "Cloud Sync", schedule_type: "daily", expression: "05:00", next_run: "2026-07-05 05:00", enabled: true },
    { id: "sch-006", operation_id: "op-007", operation_name: "Data Migration", schedule_type: "manual", expression: "-", next_run: "-", enabled: false },
  ];

  window.ScheduleStore = {
    getAll: function () { return scheduleData.slice(); },
    getById: function (id) { return findById(scheduleData, id); }
  };

  // ─── Result Store ─────────────────────────────────────
  // Sprint012 字段：id, task_id, operation_name, status, started_at, finished_at, duration, message
  var resultData = [
    { id: "res-001", task_id: "task-001", operation_name: "Daily Backup", status: "success", started_at: "2026-07-04 02:00", finished_at: "2026-07-04 02:05:30", duration: "5m30s", message: "备份完成，共 320GB" },
    { id: "res-002", task_id: "task-002", operation_name: "Daily Backup", status: "success", started_at: "2026-07-03 02:00", finished_at: "2026-07-03 02:04:45", duration: "4m45s", message: "备份完成，共 318GB" },
    { id: "res-003", task_id: "task-003", operation_name: "Daily Backup", status: "failed", started_at: "2026-07-02 02:00", finished_at: "2026-07-02 02:01:20", duration: "1m20s", message: "错误：连接超时" },
    { id: "res-004", task_id: "task-004", operation_name: "NAS Photos Backup", status: "success", started_at: "2026-07-01 03:00", finished_at: "2026-07-01 03:15:00", duration: "15m00s", message: "备份完成，共 2.1TB" },
    { id: "res-005", task_id: "task-005", operation_name: "Daily Snapshot", status: "success", started_at: "2026-07-04 01:00", finished_at: "2026-07-04 01:02:15", duration: "2m15s", message: "快照创建成功" },
    { id: "res-006", task_id: "task-006", operation_name: "Daily Snapshot", status: "success", started_at: "2026-07-03 01:00", finished_at: "2026-07-03 01:02:30", duration: "2m30s", message: "快照创建成功" },
    { id: "res-007", task_id: "task-007", operation_name: "Cloud Sync", status: "success", started_at: "2026-07-04 05:00", finished_at: "2026-07-04 05:10:00", duration: "10m00s", message: "同步完成，共 5.2TB" },
    { id: "res-008", task_id: "task-008", operation_name: "Cloud Sync", status: "running", started_at: "2026-07-03 05:00", finished_at: "", duration: "-", message: "同步中..." },
    { id: "res-009", task_id: "task-009", operation_name: "Data Migration", status: "pending", started_at: "2026-07-04 10:00", finished_at: "", duration: "-", message: "等待执行" },
  ];

  window.ResultStore = {
    getAll: function () { return resultData.slice(); },
    getById: function (id) { return findById(resultData, id); }
  };
})();
