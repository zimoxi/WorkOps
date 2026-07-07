/**
 * WorkOps Scheduler Engine — 调度引擎
 * Sprint011: Scheduler Engine Foundation
 *
 * Scheduler 负责 Operation 调度计划。
 * Scheduler 不负责执行任务、Cron、Timer、后台服务。
 *
 * 未来：Scheduler 只负责创建 Task，不直接执行 Operation。
 *
 * Read Model：只读，不提供 CRUD / Setter。
 *
 * 通过 window.SchedulerEngineModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }
  if (!window.ScheduleStore) {
    console.error("ScheduleStore not loaded.");
    return;
  }

  // ─── 调度类型定义 ──────────────────────────────────────
  var SCHEDULE_TYPES = {
    daily: { label_zh: "每天", label_en: "Daily" },
    weekly: { label_zh: "每周", label_en: "Weekly" },
    monthly: { label_zh: "每月", label_en: "Monthly" },
    manual: { label_zh: "手动", label_en: "Manual" },
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

  // ─── ScheduleStateLabel（内部实现，不迁移）──────────────
  // 配置状态 ≠ 运行状态，不使用 Components.renderStatusBadge
  function renderScheduleStateLabel(enabled) {
    var isZh = WorkOps.getLang() === "zh";
    if (enabled) {
      var label = isZh ? "启用" : "Enabled";
      return '<span class="schedule-state-label schedule-state-enabled">✓ ' + esc(label) + "</span>";
    } else {
      var label2 = isZh ? "禁用" : "Disabled";
      return '<span class="schedule-state-label schedule-state-disabled">✗ ' + esc(label2) + "</span>";
    }
  }

  // ─── Schedule Summary ───────────────────────────────────
  function renderScheduleSummary(schedules) {
    var isZh = WorkOps.getLang() === "zh";
    var enabled = 0, disabled = 0;
    for (var i = 0; i < schedules.length; i++) {
      if (schedules[i].enabled) enabled++;
      else disabled++;
    }

    var enabledLabel = isZh ? "启用" : "Enabled";
    var disabledLabel = isZh ? "禁用" : "Disabled";
    var totalLabel = isZh ? "总计" : "Total";

    return (
      '<div class="schedule-summary">' +
      '<div class="schedule-summary-stat"><span class="schedule-summary-value text-ok">' + enabled + '</span><span class="schedule-summary-label">' + esc(enabledLabel) + "</span></div>" +
      '<div class="schedule-summary-stat"><span class="schedule-summary-value text-danger">' + disabled + '</span><span class="schedule-summary-label">' + esc(disabledLabel) + "</span></div>" +
      '<div class="schedule-summary-stat"><span class="schedule-summary-value">' + schedules.length + '</span><span class="schedule-summary-label">' + esc(totalLabel) + "</span></div>" +
      "</div>"
    );
  }

  // ─── Schedule Card ──────────────────────────────────────
  function renderScheduleCard(schedule) {
    var typeLabel = t("scheduler.type." + schedule.schedule_type) || schedule.schedule_type;

    var header =
      '<span class="schedule-card-name">' + esc(schedule.operation_name) + "</span>" +
      renderScheduleStateLabel(schedule.enabled);

    var body =
      '<div class="schedule-card-field"><span class="schedule-card-label">' + esc(t("scheduler.type")) + '</span><span class="schedule-card-value">' + esc(typeLabel) + "</span></div>" +
      '<div class="schedule-card-field"><span class="schedule-card-label">' + esc(t("scheduler.expression")) + '</span><span class="schedule-card-value">' + esc(schedule.expression) + "</span></div>" +
      '<div class="schedule-card-field"><span class="schedule-card-label">' + esc(t("scheduler.nextRun")) + '</span><span class="schedule-card-value">' + esc(schedule.next_run) + "</span></div>";

    return Components.renderCard({
      header: header,
      body: body,
      dataAttributes: { "data-operation-id": schedule.operation_id }
    });
  }

  // ─── Schedule Selector ──────────────────────────────────
  function renderScheduleSelector(selectedId, onChangeFn) {
    var isZh = WorkOps.getLang() === "zh";
    var placeholder = isZh ? "-- 请选择调度 --" : "-- Select a schedule --";
    var label = isZh ? "选择调度" : "Select Schedule";

    var schedules = ScheduleStore.getAll();
    var options = [];
    for (var i = 0; i < schedules.length; i++) {
      var s = schedules[i];
      var display = s.operation_name + " (" + s.expression + ")";
      options.push({ value: s.id, label: display });
    }

    return Components.renderSelector({
      label: label,
      placeholder: placeholder,
      options: options,
      selectedValue: selectedId,
      onChange: onChangeFn
    });
  }

  // ─── Main Render ────────────────────────────────────────
  function renderSchedulerEngine() {
    var el = document.getElementById("scheduler");
    if (!el) return;

    var schedules = ScheduleStore.getAll();

    var html =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("scheduler.title")) + "</h2>" +
      '<p class="muted">' + esc(t("scheduler.subtitle")) + "</p>" +
      "</div>" +
      "</div>";

    // Schedule Summary
    html += renderScheduleSummary(schedules);

    // Schedule Cards
    if (schedules.length === 0) {
      html += '<p class="muted">' + esc(t("scheduler.noSchedule")) + "</p>";
    } else {
      html += '<div class="schedule-card-grid">';
      for (var i = 0; i < schedules.length; i++) {
        html += renderScheduleCard(schedules[i]);
      }
      html += "</div>";
    }

    html += "</div>";

    // Schedule Selector 预览
    html +=
      '<div class="band top-gap">' +
      '<h3>' + esc(t("scheduler.selectorLabel")) + "</h3>" +
      renderScheduleSelector("", "") +
      "</div>";

    el.innerHTML = html;
  }

  // ─── Public API（只暴露 render）─────────────────────────
  window.SchedulerEngineModule = {
    render: renderSchedulerEngine,
  };
})();
