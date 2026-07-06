/**
 * WorkOps Task Engine — 任务引擎
 * Sprint006: Task Engine Foundation
 * Sprint008: 删除兼容层，直接调用 Components
 *
 * Task 是 Operation 的一次执行实例。
 * Task 不负责执行命令，只管理生命周期和状态。
 *
 * 独立模块，不依赖后端 API。
 * MOCK_TASK_STORE 保持模块私有，不暴露 getTasks()。
 * 通过 window.TaskEngineModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }

  // ─── Mock Task Store（模块私有）─────────────────────────
  var MOCK_TASK_STORE = [
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

  // ─── Task Timeline（保持内部实现，不迁移）────────────────
  // COMPONENT_GUIDELINES 规定：三次以上重复才迁移
  // Timeline 目前只有 Task 使用，保持内部实现
  function renderTaskTimeline(tasks) {
    var sorted = tasks.slice().sort(function (a, b) {
      return b.start_time.localeCompare(a.start_time);
    });
    var recent = sorted.slice(0, 10);

    var items = "";
    for (var i = 0; i < recent.length; i++) {
      var task = recent[i];
      var isZh = WorkOps.getLang() === "zh";
      var durationText = task.status === "pending"
        ? (isZh ? "等待执行" : "Waiting")
        : task.status === "running"
          ? (isZh ? "进行中" : "In Progress")
          : task.duration;

      items +=
        '<div class="task-timeline-item">' +
        '<div class="task-timeline-header">' +
        '<span class="task-timeline-name">' + esc(task.operation_name) + "</span>" +
        Components.renderStatusBadge(task.status, "task") +
        "</div>" +
        '<div class="task-timeline-meta">' +
        esc(task.start_time) + " | " + esc(durationText) + " | " + esc(task.result) +
        "</div>" +
        "</div>";
    }

    return (
      '<div class="task-timeline">' +
      '<h3 class="task-timeline-title">' + esc(t("task.timeline")) + "</h3>" +
      '<div class="task-timeline-list">' + items + "</div>" +
      "</div>"
    );
  }

  // ─── Group Tasks by Operation ───────────────────────────
  function groupByOperation(tasks) {
    var groups = {};
    var order = [];
    for (var i = 0; i < tasks.length; i++) {
      var task = tasks[i];
      var key = task.operation_name;
      if (!groups[key]) {
        groups[key] = [];
        order.push(key);
      }
      groups[key].push(task);
    }
    return { groups: groups, order: order };
  }

  // ─── Main Render ────────────────────────────────────────
  function renderTaskEngine() {
    var el = document.getElementById("tasks");
    if (!el) return;

    var tasks = MOCK_TASK_STORE;
    var grouped = groupByOperation(tasks);

    var html =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("task.title")) + "</h2>" +
      '<p class="muted">' + esc(t("task.subtitle")) + "</p>" +
      "</div>" +
      "</div>";

    // Task Timeline（简单列表）
    if (tasks.length > 0) {
      html += renderTaskTimeline(tasks);
    } else {
      html += '<p class="muted">' + esc(t("task.noTask")) + "</p>";
    }

    // 按 Operation 分组的 Task Card
    if (tasks.length > 0) {
      for (var g = 0; g < grouped.order.length; g++) {
        var opName = grouped.order[g];
        var opTasks = grouped.groups[opName];
        html += '<div class="task-operation-group">';
        html += '<h3 class="task-operation-title">' + esc(opName) + "</h3>";
        html += '<div class="task-card-grid">';
        for (var ti = 0; ti < opTasks.length; ti++) {
          var task = opTasks[ti];
          var isZh = WorkOps.getLang() === "zh";
          var durationText = task.status === "pending"
            ? (isZh ? "等待执行" : "Waiting")
            : task.status === "running"
              ? (isZh ? "进行中" : "In Progress")
              : task.duration;
          var endText = task.end_time === "-" ? "-" : task.end_time;

          html += Components.renderCard({
            header:
              '<span class="task-card-name">' + esc(task.operation_name) + "</span>" +
              Components.renderStatusBadge(task.status, "task"),
            body:
              '<div class="task-card-field"><span class="task-card-label">' + esc(t("task.device")) + '</span><span class="task-card-value">' + esc(task.device_name) + "</span></div>" +
              '<div class="task-card-field"><span class="task-card-label">' + esc(t("task.resource")) + '</span><span class="task-card-value">' + esc(task.resource_name) + "</span></div>" +
              '<div class="task-card-field"><span class="task-card-label">' + esc(t("task.startTime")) + '</span><span class="task-card-value">' + esc(task.start_time) + "</span></div>" +
              '<div class="task-card-field"><span class="task-card-label">' + esc(t("task.endTime")) + '</span><span class="task-card-value">' + esc(endText) + "</span></div>" +
              '<div class="task-card-field"><span class="task-card-label">' + esc(t("task.duration")) + '</span><span class="task-card-value">' + esc(durationText) + "</span></div>" +
              '<div class="task-card-field"><span class="task-card-label">' + esc(t("task.result")) + '</span><span class="task-card-value">' + esc(task.result) + "</span></div>",
            dataAttributes: { "data-operation-id": task.operation_id }
          });
        }
        html += "</div></div>";
      }
    }

    html += "</div>";

    // Selector 选项
    var selectorOptions = [];
    for (var s = 0; s < MOCK_TASK_STORE.length; s++) {
      var t2 = MOCK_TASK_STORE[s];
      var date = t2.start_time.split(" ")[0];
      selectorOptions.push({ value: t2.id, label: t2.operation_name + " - " + date + " (" + t2.status + ")" });
    }

    // Task Selector 预览
    html +=
      '<div class="band top-gap">' +
      '<h3>' + esc(t("task.selectorLabel")) + "</h3>" +
      Components.renderSelector({
        label: WorkOps.getLang() === "zh" ? "选择任务" : "Select Task",
        placeholder: WorkOps.getLang() === "zh" ? "-- 请选择任务 --" : "-- Select a task --",
        options: selectorOptions,
        selectedValue: "",
        onChange: ""
      }) +
      "</div>";

    el.innerHTML = html;
  }

  // ─── Public API（只暴露 3 个方法）────────────────────────
  window.TaskEngineModule = {
    render: renderTaskEngine,
  };
})();
