/**
 * WorkOps Operation Engine — 操作引擎
 * Sprint005: Operation Engine Foundation
 * Sprint008: 删除兼容层，直接调用 Components
 *
 * 独立模块，不依赖后端 API。
 * 不依赖 DeviceRegistryModule 或 ResourceRegistryModule。
 * MOCK_OPERATION_STORE 保持模块私有，不暴露 getOperations()。
 * 通过 window.OperationEngineModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }

  // ─── Mock Operation Store（模块私有）────────────────────
  var MOCK_OPERATION_STORE = [
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

  // ─── Operation Type 定义（Operation 特有，不迁移）───────
  var OPERATION_TYPES = {
    backup: { label_zh: "备份", label_en: "Backup", bg: "#dbeafe", fg: "#1e40af" },
    restore: { label_zh: "恢复", label_en: "Restore", bg: "#dcfce7", fg: "#15803d" },
    snapshot: { label_zh: "快照", label_en: "Snapshot", bg: "#f3e8ff", fg: "#7c3aed" },
    migration: { label_zh: "迁移", label_en: "Migration", bg: "#fef3c7", fg: "#b45309" },
    verify: { label_zh: "验证", label_en: "Verify", bg: "#cffafe", fg: "#0891b2" },
    cloud_sync: { label_zh: "云同步", label_en: "Cloud Sync", bg: "#e0f2fe", fg: "#0284c7" },
  };

  // ─── Helpers ────────────────────────────────────────────
  function t(key) {
    return WorkOps.t(key);
  }

  function esc(v) {
    return String(v == null ? "" : v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ─── OperationTypeBadge（Operation 特有，不迁移）────────
  function renderOperationTypeBadge(type) {
    var def = OPERATION_TYPES[type] || { label_zh: type, label_en: type, bg: "#f3f4f6", fg: "#647084" };
    var isZh = WorkOps.getLang() === "zh";
    var label = isZh ? def.label_zh : def.label_en;
    return (
      '<span class="operation-type-badge" style="background:' + def.bg + ";color:" + def.fg + '">' +
      esc(label) +
      "</span>"
    );
  }

  // ─── Schedule Label（Operation 特有，不迁移）────────────
  var SCHEDULE_LABELS = {
    daily: { label_zh: "每天", label_en: "Daily" },
    weekly: { label_zh: "每周", label_en: "Weekly" },
    manual: { label_zh: "手动", label_en: "Manual" },
  };

  function renderScheduleLabel(schedule) {
    var def = SCHEDULE_LABELS[schedule];
    if (!def) return esc(schedule);
    var isZh = WorkOps.getLang() === "zh";
    return esc(isZh ? def.label_zh : def.label_en);
  }

  // ─── Group Operations by Device ─────────────────────────
  function groupByDevice(operations) {
    var groups = {};
    var order = [];
    for (var i = 0; i < operations.length; i++) {
      var op = operations[i];
      var key = op.device_name;
      if (!groups[key]) {
        groups[key] = [];
        order.push(key);
      }
      groups[key].push(op);
    }
    return { groups: groups, order: order };
  }

  // ─── Main Render ────────────────────────────────────────
  function renderOperationEngine() {
    var el = document.getElementById("operations");
    if (!el) return;

    var operations = MOCK_OPERATION_STORE;
    var grouped = groupByDevice(operations);

    var html =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("operation.title")) + "</h2>" +
      '<p class="muted">' + esc(t("operation.subtitle")) + "</p>" +
      "</div>" +
      "</div>";

    if (operations.length === 0) {
      html += '<p class="muted">' + esc(t("operation.noOperation")) + "</p>";
    } else {
      for (var g = 0; g < grouped.order.length; g++) {
        var deviceName = grouped.order[g];
        var deviceOps = grouped.groups[deviceName];
        html += '<div class="operation-device-group">';
        html += '<h3 class="operation-device-title">' + esc(deviceName) + "</h3>";
        html += '<div class="operation-card-grid">';
        for (var o = 0; o < deviceOps.length; o++) {
          var operation = deviceOps[o];

          html += Components.renderCard({
            header:
              '<span class="operation-card-name">' + esc(operation.name) + "</span>" +
              renderOperationTypeBadge(operation.type),
            body:
              '<div class="operation-card-field"><span class="operation-card-label">' + esc(t("operation.device")) + '</span><span class="operation-card-value">' + esc(operation.device_name) + "</span></div>" +
              '<div class="operation-card-field"><span class="operation-card-label">' + esc(t("operation.resource")) + '</span><span class="operation-card-value">' + esc(operation.resource_name) + "</span></div>" +
              '<div class="operation-card-field"><span class="operation-card-label">' + esc(t("operation.schedule")) + '</span><span class="operation-card-value">' + renderScheduleLabel(operation.schedule) + "</span></div>" +
              '<div class="operation-card-field"><span class="operation-card-label">' + esc(t("operation.lastRun")) + '</span><span class="operation-card-value">' + esc(operation.last_run) + "</span></div>" +
              '<div class="operation-card-field"><span class="operation-card-label">' + esc(t("operation.status")) + '</span><span class="operation-card-value">' + Components.renderStatusBadge(operation.status, "operation") + "</span></div>",
            dataAttributes: { "data-operation-id": operation.id }
          });
        }
        html += "</div></div>";
      }
    }

    html += "</div>";

    // Selector 选项
    var selectorOptions = [];
    for (var s = 0; s < MOCK_OPERATION_STORE.length; s++) {
      var op = MOCK_OPERATION_STORE[s];
      selectorOptions.push({ value: op.id, label: op.name + " (" + op.device_name + ")" });
    }

    // Operation Selector 预览
    html +=
      '<div class="band top-gap">' +
      '<h3>' + esc(t("operation.selectorLabel")) + "</h3>" +
      Components.renderSelector({
        label: WorkOps.getLang() === "zh" ? "选择操作" : "Select Operation",
        placeholder: WorkOps.getLang() === "zh" ? "-- 请选择操作 --" : "-- Select an operation --",
        options: selectorOptions,
        selectedValue: "",
        onChange: ""
      }) +
      "</div>";

    el.innerHTML = html;
  }

  // ─── Public API（只暴露 3 个方法）────────────────────────
  window.OperationEngineModule = {
    render: renderOperationEngine,
  };
})();
