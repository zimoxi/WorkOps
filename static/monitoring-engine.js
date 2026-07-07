/**
 * WorkOps Monitoring Engine — 监控引擎
 * Sprint009: Monitoring Engine Foundation
 *
 * Monitoring 负责展示系统运行状态。
 * Monitoring 不负责修改数据、执行任务、调度任务。
 *
 * Read Model：只读，不提供 CRUD / Setter。
 * MOCK_MONITOR_STORE 模块私有，不暴露 getMonitors()。
 *
 * 通过 window.MonitoringEngineModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }

  // ─── Mock Monitor Store（模块私有）──────────────────────
  // 严格遵循 Sprint009 规格：id, target_type, target_name, status, message, updated_at
  // 不使用 metric / value 字段
  // CPU / Memory / Disk / Temperature 信息放入 message
  var MOCK_MONITOR_STORE = [
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

  // ─── 按 target_type 分组 ────────────────────────────────
  function groupByType(items) {
    var groups = {};
    var order = [];
    for (var i = 0; i < items.length; i++) {
      var item = items[i];
      var key = item.target_type;
      if (!groups[key]) {
        groups[key] = [];
        order.push(key);
      }
      groups[key].push(item);
    }
    return { groups: groups, order: order };
  }

  // ─── 计算 Summary 统计 ─────────────────────────────────
  function calculateSummary(items) {
    var online = 0, warning = 0, offline = 0;
    for (var i = 0; i < items.length; i++) {
      var s = items[i].status;
      if (s === "online" || s === "success") online++;
      else if (s === "warning" || s === "running") warning++;
      else if (s === "offline" || s === "failed") offline++;
    }
    return { online: online, warning: warning, offline: offline, total: items.length };
  }

  // ─── Summary Card ───────────────────────────────────────
  function renderSummaryCard(typeLabel, summary) {
    var isZh = WorkOps.getLang() === "zh";
    var onlineLabel = isZh ? "正常" : "Normal";
    var warningLabel = isZh ? "警告" : "Warning";
    var offlineLabel = isZh ? "离线" : "Offline";

    return (
      '<div class="monitor-summary-card">' +
      '<h4 class="monitor-summary-title">' + esc(typeLabel) + "</h4>" +
      '<div class="monitor-summary-stats">' +
      '<div class="monitor-summary-stat"><span class="monitor-summary-value text-ok">' + summary.online + '</span><span class="monitor-summary-label">' + esc(onlineLabel) + "</span></div>" +
      '<div class="monitor-summary-stat"><span class="monitor-summary-value text-warn">' + summary.warning + '</span><span class="monitor-summary-label">' + esc(warningLabel) + "</span></div>" +
      '<div class="monitor-summary-stat"><span class="monitor-summary-value text-danger">' + summary.offline + '</span><span class="monitor-summary-label">' + esc(offlineLabel) + "</span></div>" +
      "</div>" +
      "</div>"
    );
  }

  // ─── Health Card ────────────────────────────────────────
  function renderHealthCard(monitor) {
    var header =
      '<span class="monitor-card-name">' + esc(monitor.target_name) + "</span>" +
      Components.renderStatusBadge(monitor.status, monitor.target_type);

    var body =
      '<div class="monitor-card-field"><span class="monitor-card-label">' + esc(t("monitor.message")) + '</span><span class="monitor-card-value">' + esc(monitor.message) + "</span></div>" +
      '<div class="monitor-card-field"><span class="monitor-card-label">' + esc(t("monitor.updatedAt")) + '</span><span class="monitor-card-value">' + esc(monitor.updated_at) + "</span></div>";

    return Components.renderCard({
      header: header,
      body: body,
      dataAttributes: { "data-monitor-id": monitor.id, "data-target-type": monitor.target_type }
    });
  }

  // ─── Monitor Widget ─────────────────────────────────────
  function renderMonitorWidget(monitors) {
    var isZh = WorkOps.getLang() === "zh";

    // 统计
    var deviceSummary = calculateSummary(monitors.filter(function (m) { return m.target_type === "device"; }));
    var operationRunning = monitors.filter(function (m) { return m.target_type === "operation" && m.status === "running"; });
    var taskRunning = monitors.filter(function (m) { return m.target_type === "task" && m.status === "running"; });
    var deviceWarning = monitors.filter(function (m) { return m.target_type === "device" && m.status === "warning"; });

    var statusText = isZh
      ? deviceSummary.online + "/" + deviceSummary.total + " 设备在线"
      : deviceSummary.online + "/" + deviceSummary.total + " devices online";

    var lastOpText = operationRunning.length > 0
      ? (isZh ? "运行中：" + operationRunning[0].target_name : "Running: " + operationRunning[0].target_name)
      : (isZh ? "无运行中操作" : "No running operations");

    var runningTaskText = taskRunning.length > 0
      ? (isZh ? "运行中：" + taskRunning[0].target_name : "Running: " + taskRunning[0].target_name)
      : (isZh ? "无运行中任务" : "No running tasks");

    var warningText = deviceWarning.length > 0
      ? (isZh ? "警告设备：" + deviceWarning[0].target_name + " - " + deviceWarning[0].message : "Warning: " + deviceWarning[0].target_name + " - " + deviceWarning[0].message)
      : (isZh ? "无警告" : "No warnings");

    return (
      '<div class="monitor-widget">' +
      '<h3 class="monitor-widget-title">' + esc(t("monitor.widget")) + "</h3>" +
      '<div class="monitor-widget-body">' +
      '<div class="monitor-widget-row"><span class="monitor-widget-label">' + esc(t("monitor.widget.deviceStatus")) + '</span><span class="monitor-widget-value">' + esc(statusText) + "</span></div>" +
      '<div class="monitor-widget-row"><span class="monitor-widget-label">' + esc(t("monitor.widget.lastOperation")) + '</span><span class="monitor-widget-value">' + esc(lastOpText) + "</span></div>" +
      '<div class="monitor-widget-row"><span class="monitor-widget-label">' + esc(t("monitor.widget.runningTask")) + '</span><span class="monitor-widget-value">' + esc(runningTaskText) + "</span></div>" +
      '<div class="monitor-widget-row"><span class="monitor-widget-label">' + esc(t("monitor.widget.warning")) + '</span><span class="monitor-widget-value">' + esc(warningText) + "</span></div>" +
      "</div>" +
      "</div>"
    );
  }

  // ─── Target Type 标签 ──────────────────────────────────
  var TARGET_TYPE_LABELS = {
    device: { label_zh: "设备", label_en: "Device" },
    resource: { label_zh: "资源", label_en: "Resource" },
    operation: { label_zh: "操作", label_en: "Operation" },
    task: { label_zh: "任务", label_en: "Task" },
  };

  function getTargetTypeLabel(type) {
    var def = TARGET_TYPE_LABELS[type];
    if (!def) return type;
    var isZh = WorkOps.getLang() === "zh";
    return isZh ? def.label_zh : def.label_en;
  }

  // ─── Main Render ────────────────────────────────────────
  function renderMonitoringEngine() {
    var el = document.getElementById("monitoring");
    if (!el) return;

    var monitors = MOCK_MONITOR_STORE;
    var grouped = groupByType(monitors);

    var html =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("monitor.title")) + "</h2>" +
      '<p class="muted">' + esc(t("monitor.subtitle")) + "</p>" +
      "</div>" +
      "</div>";

    // System Health Summary
    html += '<div class="monitor-summary-grid">';
    for (var s = 0; s < grouped.order.length; s++) {
      var type = grouped.order[s];
      var typeItems = grouped.groups[type];
      var summary = calculateSummary(typeItems);
      html += renderSummaryCard(getTargetTypeLabel(type), summary);
    }
    html += "</div>";

    // 按 target_type 分组的 Health Card
    for (var g = 0; g < grouped.order.length; g++) {
      var targetType = grouped.order[g];
      var targetItems = grouped.groups[targetType];
      html += '<div class="monitor-type-group">';
      html += '<h3 class="monitor-type-title">' + esc(getTargetTypeLabel(targetType)) + esc(t("monitor.health")) + "</h3>";
      html += '<div class="monitor-card-grid">';
      for (var h = 0; h < targetItems.length; h++) {
        html += renderHealthCard(targetItems[h]);
      }
      html += "</div></div>";
    }

    html += "</div>";

    // Monitor Widget
    html +=
      '<div class="band top-gap">' +
      renderMonitorWidget(monitors) +
      "</div>";

    el.innerHTML = html;
  }

  // ─── Public API（只暴露 render）─────────────────────────
  window.MonitoringEngineModule = {
    render: renderMonitoringEngine,
  };
})();
