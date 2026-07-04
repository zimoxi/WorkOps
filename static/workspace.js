/**
 * WorkOps Workspace — Mock Dashboard
 * Sprint002: Workspace Foundation
 *
 * 独立模块，不依赖后端 API。
 * 通过 window.WorkspaceModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── Mock Data ──────────────────────────────────────────
  var MOCK = {
    deviceSummary: {
      total: 7,
      online: 5,
      offline: 1,
      unknown: 1,
      alerts: 2,
    },
    recentOperations: [
      {
        id: "op1",
        type: "backup",
        device: "NAS",
        status: "success",
        time: "2026-07-04 10:30",
        label_zh: "Restic 备份完成",
        label_en: "Restic backup completed",
      },
      {
        id: "op2",
        type: "snapshot",
        device: "PVE",
        status: "success",
        time: "2026-07-04 09:15",
        label_zh: "快照创建成功",
        label_en: "Snapshot created",
      },
      {
        id: "op3",
        type: "restore",
        device: "Linux-Server",
        status: "success",
        time: "2026-07-03 22:00",
        label_zh: "恢复验证通过",
        label_en: "Restore verification passed",
      },
      {
        id: "op4",
        type: "backup",
        device: "Windows-PC",
        status: "failed",
        time: "2026-07-03 20:00",
        label_zh: "Robocopy 失败",
        label_en: "Robocopy failed",
      },
    ],
    monitoringOverview: [
      {
        device: "PVE",
        cpu: 23,
        memory: 61,
        disk: 45,
        network: "1.2 Gbps",
      },
      {
        device: "NAS",
        cpu: 8,
        memory: 72,
        disk: 78,
        network: "800 Mbps",
      },
      {
        device: "Linux-Server",
        cpu: 45,
        memory: 55,
        disk: 30,
        network: "200 Mbps",
      },
    ],
    alerts: [
      {
        id: "a1",
        severity: "warning",
        device: "NAS",
        message_zh: "SMART: 磁盘 3 温度偏高 (48°C)",
        message_en: "SMART: Disk 3 temperature high (48°C)",
        time: "2026-07-04 08:00",
      },
      {
        id: "a2",
        severity: "error",
        device: "Windows-PC",
        message_zh: "备份失败: SMB 连接超时",
        message_en: "Backup failed: SMB connection timeout",
        time: "2026-07-03 20:01",
      },
    ],
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

  function isZh() {
    return WorkOps.getLang() === "zh";
  }

  // ─── Widget Renderers ───────────────────────────────────

  function renderDeviceSummaryWidget() {
    var d = MOCK.deviceSummary;
    return (
      '<div class="widget-card">' +
      '<h3 class="widget-title">' + esc(t("workspace.deviceSummary")) + "</h3>" +
      '<div class="widget-metrics">' +
      '<div class="metric-item"><span class="metric-value">' + d.total + '</span><span class="metric-label">' + esc(t("workspace.total")) + "</span></div>" +
      '<div class="metric-item"><span class="metric-value text-ok">' + d.online + '</span><span class="metric-label">' + esc(t("workspace.online")) + "</span></div>" +
      '<div class="metric-item"><span class="metric-value text-warn">' + d.offline + '</span><span class="metric-label">' + esc(t("workspace.offline")) + "</span></div>" +
      '<div class="metric-item"><span class="metric-value text-danger">' + d.alerts + '</span><span class="metric-label">' + esc(t("workspace.alerts")) + "</span></div>" +
      "</div></div>"
    );
  }

  function renderRecentOpsWidget() {
    var ops = MOCK.recentOperations;
    var rows = "";
    for (var i = 0; i < ops.length; i++) {
      var op = ops[i];
      var label = isZh() ? op.label_zh : op.label_en;
      var statusClass = op.status === "success" ? "text-ok" : "text-danger";
      rows +=
        '<div class="op-row">' +
        '<span class="op-device">' + esc(op.device) + "</span>" +
        '<span class="op-label">' + esc(label) + "</span>" +
        '<span class="op-status ' + statusClass + '">' + esc(op.status) + "</span>" +
        '<span class="op-time">' + esc(op.time) + "</span>" +
        "</div>";
    }
    return (
      '<div class="widget-card widget-wide">' +
      '<h3 class="widget-title">' + esc(t("workspace.recentOps")) + "</h3>" +
      '<div class="op-list">' +
      (rows || '<p class="muted">' + esc(t("workspace.noOps")) + "</p>") +
      "</div></div>"
    );
  }

  function renderMonitoringWidget() {
    var items = MOCK.monitoringOverview;
    var rows = "";
    for (var i = 0; i < items.length; i++) {
      var m = items[i];
      rows +=
        '<div class="mon-row">' +
        '<span class="mon-device">' + esc(m.device) + "</span>" +
        '<span class="mon-bar"><span class="mon-fill" style="width:' + m.cpu + '%"></span></span>' +
        '<span class="mon-val">' + m.cpu + "% CPU</span>" +
        '<span class="mon-bar"><span class="mon-fill" style="width:' + m.memory + '%"></span></span>' +
        '<span class="mon-val">' + m.memory + "% MEM</span>" +
        '<span class="mon-bar"><span class="mon-fill" style="width:' + m.disk + '%"></span></span>' +
        '<span class="mon-val">' + m.disk + "% DISK</span>" +
        "</div>";
    }
    return (
      '<div class="widget-card widget-wide">' +
      '<h3 class="widget-title">' + esc(t("workspace.monitoring")) + "</h3>" +
      '<div class="mon-list">' + rows + "</div></div>"
    );
  }

  function renderAlertsWidget() {
    var alerts = MOCK.alerts;
    var rows = "";
    for (var i = 0; i < alerts.length; i++) {
      var a = alerts[i];
      var msg = isZh() ? a.message_zh : a.message_en;
      var sevClass = a.severity === "error" ? "text-danger" : "text-warn";
      rows +=
        '<div class="alert-row">' +
        '<span class="alert-sev ' + sevClass + '">' + esc(a.severity) + "</span>" +
        '<span class="alert-device">' + esc(a.device) + "</span>" +
        '<span class="alert-msg">' + esc(msg) + "</span>" +
        '<span class="alert-time">' + esc(a.time) + "</span>" +
        "</div>";
    }
    return (
      '<div class="widget-card">' +
      '<h3 class="widget-title">' + esc(t("workspace.alertList")) + "</h3>" +
      '<div class="alert-list">' +
      (rows || '<p class="muted">' + esc(t("workspace.noAlerts")) + "</p>") +
      "</div></div>"
    );
  }

  function renderQuickActionsWidget() {
    return (
      '<div class="widget-card">' +
      '<h3 class="widget-title">' + esc(t("workspace.quickActions")) + "</h3>" +
      '<div class="quick-actions">' +
      '<button class="secondary" onclick="showPage(\'devices\')">' + esc(t("workspace.addDevice")) + "</button>" +
      '<button class="secondary">' + esc(t("workspace.newOperation")) + "</button>" +
      '<button class="secondary" onclick="showPage(\'jobs\')">' + esc(t("workspace.viewTasks")) + "</button>" +
      "</div></div>"
    );
  }

  // ─── Main Render ────────────────────────────────────────

  function renderWorkspace() {
    var el = document.getElementById("workspace");
    if (!el) return;
    el.innerHTML =
      '<div class="widget-grid">' +
      renderDeviceSummaryWidget() +
      renderRecentOpsWidget() +
      renderMonitoringWidget() +
      renderAlertsWidget() +
      renderQuickActionsWidget() +
      "</div>";
  }

  // ─── Mobile Menu Toggle ──────────────────────────────────
  function toggleMenu() {
    var sidebar = document.getElementById("sidebar");
    var overlay = document.getElementById("menuOverlay");
    if (sidebar) sidebar.classList.toggle("open");
    if (overlay) overlay.classList.toggle("open");
  }

  // Close menu when a nav button is clicked (mobile)
  document.addEventListener("click", function (e) {
    if (e.target.classList && e.target.classList.contains("nav")) {
      var sidebar = document.getElementById("sidebar");
      var overlay = document.getElementById("menuOverlay");
      if (sidebar && sidebar.classList.contains("open")) {
        sidebar.classList.remove("open");
        if (overlay) overlay.classList.remove("open");
      }
    }
  });

  // ─── Public API ─────────────────────────────────────────
  window.WorkspaceModule = {
    renderWorkspace: renderWorkspace,
  };
  window.toggleMenu = toggleMenu;
})();
