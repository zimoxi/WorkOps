/**
 * WorkOps Resource Registry — 资源注册中心
 * Sprint004: Resource Registry Foundation
 * Sprint008: 删除兼容层，直接调用 Components
 * Sprint010: 从 ResourceStore 读取数据
 *
 * 独立模块，不依赖后端 API。
 * 不依赖 DeviceRegistryModule（避免跨模块 UI 依赖）。
 * 通过 window.ResourceRegistryModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }
  if (!window.ResourceStore) {
    console.error("ResourceStore not loaded.");
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

  // ─── Group Resources by Device ──────────────────────────
  function groupByDevice(resources) {
    var groups = {};
    var order = [];
    for (var i = 0; i < resources.length; i++) {
      var r = resources[i];
      var key = r.device_name;
      if (!groups[key]) {
        groups[key] = [];
        order.push(key);
      }
      groups[key].push(r);
    }
    return { groups: groups, order: order };
  }

  // ─── Main Render ────────────────────────────────────────
  function renderResourceRegistry() {
    var el = document.getElementById("resources");
    if (!el) return;

    var resources = ResourceStore.getAll();
    var grouped = groupByDevice(resources);

    var html =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("resource.title")) + "</h2>" +
      '<p class="muted">' + esc(t("resource.subtitle")) + "</p>" +
      "</div>" +
      "</div>";

    if (resources.length === 0) {
      html += '<p class="muted">' + esc(t("resource.noResource")) + "</p>";
    } else {
      for (var g = 0; g < grouped.order.length; g++) {
        var deviceName = grouped.order[g];
        var deviceResources = grouped.groups[deviceName];
        html += '<div class="resource-device-group">';
        html += '<h3 class="resource-device-title">' + esc(deviceName) + "</h3>";
        html += '<div class="resource-card-grid">';
        for (var r = 0; r < deviceResources.length; r++) {
          var resource = deviceResources[r];
          var typeLabel = t("resource.type." + resource.type) || resource.type;
          var capacityText = resource.size_total !== "-"
            ? esc(resource.size_used) + " / " + esc(resource.size_total)
            : "-";

          html += Components.renderCard({
            header:
              '<span class="resource-card-name">' + esc(resource.name) + "</span>" +
              Components.renderStatusBadge(resource.status, "resource"),
            body:
              '<div class="resource-card-field"><span class="resource-card-label">' + esc(t("resource.type")) + '</span><span class="resource-card-value">' + esc(typeLabel) + "</span></div>" +
              '<div class="resource-card-field"><span class="resource-card-label">' + esc(t("resource.path")) + '</span><span class="resource-card-value">' + esc(resource.path) + "</span></div>" +
              '<div class="resource-card-field"><span class="resource-card-label">' + esc(t("resource.capacity")) + '</span><span class="resource-card-value">' + capacityText + "</span></div>",
            dataAttributes: { "data-device-id": resource.device_id }
          });
        }
        html += "</div></div>";
      }
    }

    html += "</div>";

    // Selector 选项
    var selectorOptions = [];
    for (var s = 0; s < resources.length; s++) {
      var res = resources[s];
      selectorOptions.push({ value: res.id, label: res.name + " (" + res.device_name + ")" });
    }

    // Resource Selector 预览
    html +=
      '<div class="band top-gap">' +
      '<h3>' + esc(t("resource.selectorLabel")) + "</h3>" +
      Components.renderSelector({
        label: WorkOps.getLang() === "zh" ? "选择资源" : "Select Resource",
        placeholder: WorkOps.getLang() === "zh" ? "-- 请选择资源 --" : "-- Select a resource --",
        options: selectorOptions,
        selectedValue: "",
        onChange: ""
      }) +
      "</div>";

    el.innerHTML = html;
  }

  // ─── Public API ─────────────────────────────────────────
  window.ResourceRegistryModule = {
    render: renderResourceRegistry,
  };
})();
