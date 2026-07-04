(function () {
  var STEP_PAGES = {
    connect: "storage",
    storage: "storage",
    restore_root: "restore",
    dataset: "migration",
    restic: "nas",
    first_backup: "nas",
    restore_center: "restore",
    schedule: "nas",
    windows: "windows",
    cloud: "cloud",
    pve_pbs: "pve",
  };

  function safe(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function statusLabel(status) {
    return WorkOps.t("status." + status) || WorkOps.t("status.not_started");
  }

  function stepById(workflow, stepId) {
    return workflow?.steps?.find(function (step) { return step.id === stepId; }) || null;
  }

  function renderStatus(step) {
    return '<span class="step-status ' + safe(step.status) + '"><span class="status-mark" aria-hidden="true"></span>' + safe(statusLabel(step.status)) + '</span>';
  }

  function renderOverview(workflow) {
    if (!workflow?.steps?.length) {
      return '<div class="workflow-empty">' + safe(WorkOps.t("overview.workflowEmpty")) + '</div>';
    }
    var percent = Math.round((workflow.completed_count / workflow.total_count) * 100);
    var nextStepHtml = "";
    if (workflow.next_step) {
      nextStepHtml = '<div class="workflow-next"><span>' + safe(WorkOps.t("overview.suggestNext")) + safe(stepById(workflow, workflow.next_step)?.title || "") + '</span><button onclick="openWorkflowStep(\'' + safe(workflow.next_step) + '\')">' + safe(WorkOps.t("btn.continue")) + '</button></div>';
    } else {
      nextStepHtml = '<div class="workflow-next complete"><strong>' + safe(WorkOps.t("overview.allDone")) + '</strong></div>';
    }
    return '\n      <section class="workflow-panel" aria-labelledby="workflowTitle">\n        <div class="workflow-heading">\n          <div>\n            <p class="eyebrow">' + safe(WorkOps.t("overview.workflowLabel")) + '</p>\n            <h1 id="workflowTitle">' + safe(WorkOps.t("overview.workflowTitle")) + '</h1>\n            <p class="muted">' + safe(WorkOps.t("overview.workflowDesc")) + '</p>\n          </div>\n          <div class="workflow-progress" aria-label="' + safe(WorkOps.t("overview.processed")) + " " + workflow.completed_count + " / " + workflow.total_count + '">\n            <strong>' + workflow.completed_count + '/' + workflow.total_count + '</strong>\n            <span>' + safe(WorkOps.t("overview.processed")) + '</span>\n          </div>\n        </div>\n        <div class="progress-track" aria-hidden="true"><span style="width:' + percent + '%"></span></div>\n        <div class="workflow-list">\n          ' + workflow.steps.map(function (step, index) {
            return '\n            <div class="workflow-row ' + (step.id === workflow.next_step ? "current" : "") + '">\n              <span class="step-number">' + (index + 1) + '</span>\n              <div class="step-copy">\n                <strong>' + safe(step.title) + '</strong>\n                ' + (step.optional ? '<span class="optional-label">' + safe(WorkOps.t("overview.optional")) + '</span>' : "") + '\n                ' + (step.skip_reason ? '<small>' + safe(step.skip_reason) + '</small>' : "") + '\n              </div>\n              ' + renderStatus(step) + '\n              <button class="secondary compact" onclick="openWorkflowStep(\'' + safe(step.id) + '\')">' + safe(WorkOps.t("btn.open")) + '</button>\n            </div>';
          }).join("") + '\n        </div>\n        ' + nextStepHtml + '\n      </section>';
  }

  function renderStepHeader(stepId, workflow, description, prerequisites) {
    prerequisites = prerequisites || [];
    var step = stepById(workflow, stepId);
    var index = workflow?.steps?.findIndex(function (item) { return item.id === stepId; }) ?? -1;
    var total = workflow?.total_count || 11;
    return '\n      <div class="step-header">\n        <div class="step-header-main">\n          <p class="eyebrow">' + safe(WorkOps.tf("overview.stepOf", { n: index + 1, total: total })) + '</p>\n          <h2>' + safe(step?.title || stepId) + '</h2>\n          <p class="muted">' + safe(description) + '</p>\n        </div>\n        ' + (step ? renderStatus(step) : "") + '\n        ' + (prerequisites.length ? '<div class="prerequisite-list"><strong>' + safe(WorkOps.t("overview.suggestStep").replace("：", "").replace(":", "").trim() || "开始前检查") + '</strong><ul>' + prerequisites.map(function (item) { return '<li>' + safe(item) + '</li>'; }).join("") + '</ul></div>' : "") + '\n      </div>';
  }

  function renderFieldHelp(options) {
    options = options || {};
    var purpose = options.purpose || "";
    var example = options.example || "";
    var format = options.format || "";
    var safety = options.safety || "";
    return '<div class="field-help">\n      ' + (purpose ? '<span>' + safe(purpose) + '</span>' : "") + '\n      ' + (example ? '<span><strong>' + safe(WorkOps.getLang() === "en" ? "Example:" : "示例：") + '</strong><code>' + safe(example) + '</code></span>' : "") + '\n      ' + (format ? '<span><strong>' + safe(WorkOps.getLang() === "en" ? "Format:" : "格式：") + '</strong>' + safe(format) + '</span>' : "") + '\n      ' + (safety ? '<span class="field-safety"><strong>' + safe(WorkOps.getLang() === "en" ? "Warning:" : "注意：") + '</strong>' + safe(safety) + '</span>' : "") + '\n    </div>';
  }

  function renderStepFooter(stepId, workflow) {
    var step = stepById(workflow, stepId);
    if (!step) return "";
    var index = workflow.steps.findIndex(function (item) { return item.id === stepId; });
    var next = workflow.steps.slice(index + 1).find(function (item) { return ["skipped", "unavailable"].indexOf(item.status) === -1; });
    var optionalAction = "";
    if (step.optional) {
      if (step.status === "skipped") {
        optionalAction = '<button class="secondary" onclick="reopenWorkflowStep(\'' + safe(stepId) + '\')">' + safe(WorkOps.t("btn.reopen")) + '</button>';
      } else if (step.status !== "unavailable") {
        optionalAction = '<button class="secondary" onclick="skipWorkflowStep(\'' + safe(stepId) + '\')">' + safe(WorkOps.t("btn.skip")) + '</button>';
      }
    }
    return '<div class="step-footer">\n      <div><strong>' + safe(WorkOps.getLang() === "en" ? "Completion Criteria" : "完成标准") + '</strong><p>' + safe(completionText(stepId)) + '</p></div>\n      <div class="actions">' + optionalAction + (next ? '<button onclick="openWorkflowStep(\'' + safe(next.id) + '\')">' + safe(WorkOps.t("btn.continue")) + "：" + safe(next.title) + '</button>' : "") + '</div>\n    </div>';
  }

  function completionText(stepId) {
    return WorkOps.t("completion." + stepId) || WorkOps.t("completion.default");
  }

  window.BackupWorkflow = {
    STEP_PAGES: STEP_PAGES,
    renderOverview: renderOverview,
    renderStepHeader: renderStepHeader,
    renderFieldHelp: renderFieldHelp,
    renderStepFooter: renderStepFooter,
    statusLabel: statusLabel,
    stepById: stepById,
  };
})();
