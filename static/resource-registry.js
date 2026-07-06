/**
 * WorkOps Resource Registry — 资源注册中心
 * Sprint004: Resource Registry Foundation
 * Sprint008: 删除兼容层，直接调用 Components
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

  // ─── Mock Resource Store ────────────────────────────────
  var MOCK_RESOURCE_STORE = [
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

    var resources = MOCK_RESOURCE_STORE;
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
    for (var s = 0; s < MOCK_RESOURCE_STORE.length; s++) {
      var res = MOCK_RESOURCE_STORE[s];
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
    getResources: function () { return MOCK_RESOURCE_STORE; },
  };
})();
