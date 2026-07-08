/**
 * WorkOps History & Result Engine — 历史与结果引擎
 * Sprint012: History & Result Engine Foundation
 *
 * History & Result 负责任务执行历史记录和结果展示。
 * 不负责执行任务、调度任务、修改数据。
 *
 * Read Model：只读，不提供 CRUD / Setter。
 *
 * 通过 window.HistoryEngineModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }
  if (!window.ResultStore) {
    console.error("ResultStore not loaded.");
    return;
  }

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

  // ─── calculateSummary（可复用，为 Dashboard/Monitoring/Notification 准备）──
  function calculateSummary(results) {
    var success = 0, failed = 0, running = 0, pending = 0;
    for (var i = 0; i < results.length; i++) {
      var s = results[i].status;
      if (s === "success") success++;
      else if (s === "failed") failed++;
      else if (s === "running") running++;
      else if (s === "pending") pending++;
    }
    return { success: success, failed: failed, running: running, pending: pending, total: results.length };
  }

  // ─── Result Summary ─────────────────────────────────────
  function renderHistorySummary(results) {
    var summary = calculateSummary(results);
    var isZh = WorkOps.getLang() === "zh";
    var successLabel = isZh ? "成功" : "Success";
    var failedLabel = isZh ? "失败" : "Failed";
    var runningLabel = isZh ? "运行中" : "Running";
    var pendingLabel = isZh ? "等待中" : "Pending";

    return (
      '<div class="history-summary">' +
      '<div class="history-summary-stat"><span class="history-summary-value text-ok">' + summary.success + '</span><span class="history-summary-label">' + esc(successLabel) + "</span></div>" +
      '<div class="history-summary-stat"><span class="history-summary-value text-danger">' + summary.failed + '</span><span class="history-summary-label">' + esc(failedLabel) + "</span></div>" +
      '<div class="history-summary-stat"><span class="history-summary-value text-warn">' + summary.running + '</span><span class="history-summary-label">' + esc(runningLabel) + "</span></div>" +
      '<div class="history-summary-stat"><span class="history-summary-value">' + summary.pending + '</span><span class="history-summary-label">' + esc(pendingLabel) + "</span></div>" +
      "</div>"
    );
  }

  // ─── Result Card（带 data-result-id 和 data-task-id）───
  function renderResultCard(result) {
    var isZh = WorkOps.getLang() === "zh";
    var durationText = result.status === "pending"
      ? (isZh ? "等待执行" : "Waiting")
      : result.status === "running"
        ? (isZh ? "进行中" : "In Progress")
        : result.duration;

    var finishedText = result.finished_at || "-";

    var header =
      '<span class="result-card-name">' + esc(result.operation_name) + "</span>" +
      Components.renderStatusBadge(result.status, "task");

    var body =
      '<div class="result-card-field"><span class="result-card-label">' + esc(t("history.startedAt")) + '</span><span class="result-card-value">' + esc(result.started_at) + "</span></div>" +
      '<div class="result-card-field"><span class="result-card-label">' + esc(t("history.finishedAt")) + '</span><span class="result-card-value">' + esc(finishedText) + "</span></div>" +
      '<div class="result-card-field"><span class="result-card-label">' + esc(t("history.duration")) + '</span><span class="result-card-value">' + esc(durationText) + "</span></div>" +
      '<div class="result-card-field"><span class="result-card-label">' + esc(t("history.message")) + '</span><span class="result-card-value">' + esc(result.message) + "</span></div>";

    return Components.renderCard({
      header: header,
      body: body,
      dataAttributes: { "data-result-id": result.id, "data-task-id": result.task_id }
    });
  }

  // ─── History Timeline（按 started_at 倒序，最多 20 条）──
  function renderHistoryTimeline(results) {
    var sorted = results.slice().sort(function (a, b) {
      return (b.started_at || "").localeCompare(a.started_at || "");
    });
    var recent = sorted.slice(0, 20);

    var items = "";
    for (var i = 0; i < recent.length; i++) {
      var result = recent[i];
      var isZh = WorkOps.getLang() === "zh";
      var durationText = result.status === "pending"
        ? (isZh ? "等待执行" : "Waiting")
        : result.status === "running"
          ? (isZh ? "进行中" : "In Progress")
          : result.duration;

      items +=
        '<div class="history-timeline-item">' +
        '<div class="history-timeline-header">' +
        '<span class="history-timeline-name">' + esc(result.operation_name) + "</span>" +
        Components.renderStatusBadge(result.status, "task") +
        "</div>" +
        '<div class="history-timeline-meta">' +
        esc(result.started_at) + " | " + esc(durationText) + " | " + esc(result.message) +
        "</div>" +
        "</div>";
    }

    return (
      '<div class="history-timeline">' +
      '<h3 class="history-timeline-title">' + esc(t("history.timeline")) + "</h3>" +
      '<div class="history-timeline-list">' + items + "</div>" +
      "</div>"
    );
  }

  // ─── Result Selector ────────────────────────────────────
  function renderResultSelector(selectedId, onChangeFn) {
    var isZh = WorkOps.getLang() === "zh";
    var placeholder = isZh ? "-- 请选择结果 --" : "-- Select a result --";
    var label = isZh ? "选择结果" : "Select Result";

    var results = ResultStore.getAll();
    var options = [];
    for (var i = 0; i < results.length; i++) {
      var r = results[i];
      var display = r.operation_name + " - " + (r.started_at || "").split(" ")[0] + " (" + r.status + ")";
      options.push({ value: r.id, label: display });
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
  function renderHistoryEngine() {
    var el = document.getElementById("history");
    if (!el) return;

    var results = ResultStore.getAll();

    var html =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("history.title")) + "</h2>" +
      '<p class="muted">' + esc(t("history.subtitle")) + "</p>" +
      "</div>" +
      "</div>";

    // History Summary
    html += renderHistorySummary(results);

    // History Timeline（按 started_at 倒序，最多 20 条）
    if (results.length > 0) {
      html += renderHistoryTimeline(results);
    } else {
      html += '<p class="muted">' + esc(t("history.noHistory")) + "</p>";
    }

    // Result Cards
    if (results.length > 0) {
      var sorted = results.slice().sort(function (a, b) {
        return (b.started_at || "").localeCompare(a.started_at || "");
      });
      html += '<div class="result-card-grid">';
      for (var i = 0; i < sorted.length; i++) {
        html += renderResultCard(sorted[i]);
      }
      html += "</div>";
    }

    html += "</div>";

    // Result Selector 预览
    html +=
      '<div class="band top-gap">' +
      '<h3>' + esc(t("history.selectorLabel")) + "</h3>" +
      renderResultSelector("", "") +
      "</div>";

    el.innerHTML = html;
  }

  // ─── Public API（只暴露 render）─────────────────────────
  window.HistoryEngineModule = {
    render: renderHistoryEngine,
  };
})();
