/**
 * WorkOps Component Library — 组件库
 * Sprint007: Component Library Foundation
 *
 * 所有公共组件统一放在此文件中。
 * 通过 window.Components 暴露给业务模块。
 *
 * 设计原则：
 * - 组件只负责渲染，不负责业务逻辑
 * - 组件不直接依赖 WorkOps，通过内部封装获取语言
 * - 组件使用 .components- 命名空间避免样式冲突
 */
(function () {
  "use strict";

  // ─── 语言封装（不直接依赖 WorkOps）──────────────────────
  function getLang() {
    try {
      if (typeof WorkOps !== "undefined" && WorkOps.getLang) {
        return WorkOps.getLang();
      }
    } catch (e) {}
    return "zh";
  }

  // ─── 工具函数 ────────────────────────────────────────
  function esc(v) {
    return String(v == null ? "" : v)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  // ─── StatusBadge ─────────────────────────────────────
  var STATUS_COLORS = {
    // Device / Resource 状态
    online: { bg: "#dcfce7", fg: "#15803d", label_zh: "在线", label_en: "Online" },
    offline: { bg: "#fee2e2", fg: "#b91c1c", label_zh: "离线", label_en: "Offline" },
    warning: { bg: "#fef3c7", fg: "#b45309", label_zh: "警告", label_en: "Warning" },
    // Operation / Task 状态
    success: { bg: "#dcfce7", fg: "#15803d", label_zh: "成功", label_en: "Success" },
    failed: { bg: "#fee2e2", fg: "#b91c1c", label_zh: "失败", label_en: "Failed" },
    pending: { bg: "#fef3c7", fg: "#b45309", label_zh: "等待中", label_en: "Pending" },
    running: { bg: "#dbeafe", fg: "#1e40af", label_zh: "执行中", label_en: "Running" },
    cancelled: { bg: "#f3f4f6", fg: "#647084", label_zh: "已取消", label_en: "Cancelled" },
    unknown: { bg: "#f3f4f6", fg: "#647084", label_zh: "未知", label_en: "Unknown" },
  };

  /**
   * 渲染状态徽章
   * @param {string} status - 状态值
   * @param {string} type - 类型（device/resource/operation/task），保留参数，暂不使用
   * @returns {string} HTML 字符串
   */
  function renderStatusBadge(status, type) {
    var s = STATUS_COLORS[status] || STATUS_COLORS.unknown;
    var isZh = getLang() === "zh";
    var label = isZh ? s.label_zh : s.label_en;
    return (
      '<span class="components-status-badge" style="background:' + s.bg + ";color:" + s.fg + '">' +
      "● " + esc(label) +
      "</span>"
    );
  }

  // ─── Card（只负责布局）──────────────────────────────
  /**
   * 渲染卡片（只负责布局，不负责 Registry 字段）
   * @param {Object} options
   * @param {string} options.header - 卡片头部 HTML
   * @param {string} options.body - 卡片正文 HTML
   * @param {string} [options.footer] - 卡片底部 HTML
   * @param {Object} [options.dataAttributes] - HTML 属性
   * @returns {string} HTML 字符串
   */
  function renderCard(options) {
    var header = options.header || "";
    var body = options.body || "";
    var footer = options.footer || "";
    var dataAttrs = "";

    if (options.dataAttributes) {
      for (var key in options.dataAttributes) {
        if (options.dataAttributes.hasOwnProperty(key)) {
          dataAttrs += " " + key + '="' + esc(options.dataAttributes[key]) + '"';
        }
      }
    }

    return (
      '<div class="components-card"' + dataAttrs + ">" +
      (header ? '<div class="components-card-header">' + header + "</div>" : "") +
      (body ? '<div class="components-card-body">' + body + "</div>" : "") +
      (footer ? '<div class="components-card-footer">' + footer + "</div>" : "") +
      "</div>"
    );
  }

  // ─── Selector ───────────────────────────────────────
  /**
   * 渲染选择器
   * @param {Object} options
   * @param {string} options.label - 标签文字
   * @param {string} options.placeholder - 占位符
   * @param {Array} options.options - 选项数组 [{value, label}]
   * @param {string} [options.selectedValue] - 选中值
   * @param {string} [options.onChange] - onChange 函数名
   * @returns {string} HTML 字符串
   */
  function renderSelector(options) {
    var label = options.label || "";
    var placeholder = options.placeholder || "-- Select --";
    var opts = options.options || [];
    var selectedValue = options.selectedValue || "";
    var onChange = options.onChange || "";

    var optionsHtml = '<option value="">' + esc(placeholder) + "</option>";
    for (var i = 0; i < opts.length; i++) {
      var selected = opts[i].value === selectedValue ? " selected" : "";
      optionsHtml += '<option value="' + esc(opts[i].value) + '"' + selected + ">" + esc(opts[i].label) + "</option>";
    }

    var onchange = onChange ? ' onchange="' + esc(onChange) + '(this.value)"' : "";

    return (
      '<div class="components-selector">' +
      (label ? '<label class="components-selector-label">' + esc(label) + "</label>" : "") +
      '<select class="components-selector-select"' + onchange + ">" + optionsHtml + "</select>" +
      "</div>"
    );
  }

  // ─── Loading ────────────────────────────────────────
  /**
   * 渲染加载动画
   * @returns {string} HTML 字符串
   */
  function renderLoading() {
    return '<div class="components-loading"><div class="components-loading-spinner"></div></div>';
  }

  // ─── EmptyState ─────────────────────────────────────
  /**
   * 渲染空状态
   * @param {string} message - 提示文字
   * @returns {string} HTML 字符串
   */
  function renderEmptyState(message) {
    return '<div class="components-empty-state"><p class="components-empty-state-message">' + esc(message) + "</p></div>";
  }

  // ─── Public API ─────────────────────────────────────
  window.Components = {
    renderStatusBadge: renderStatusBadge,
    renderCard: renderCard,
    renderSelector: renderSelector,
    renderLoading: renderLoading,
    renderEmptyState: renderEmptyState,
  };
})();
