/**
 * WorkOps Device Registry — 设备注册中心
 * Sprint003: Device Registry Foundation
 * Sprint008: 删除兼容层，直接调用 Components
 *
 * 独立模块，不依赖后端 API。
 * 通过 window.DeviceRegistryModule 暴露给 app.js。
 */
(function () {
  "use strict";

  // ─── 模块级安全检查 ────────────────────────────────────
  if (!window.Components) {
    console.error("Components library not loaded.");
    return;
  }

  // ─── Mock Device Store ──────────────────────────────────
  var MOCK_DEVICE_STORE = [
    { id: "550e8400-e29b-41d4-a716-446655440001", name: "Windows-PC", type: "windows", status: "online", ip: "192.168.1.100" },
    { id: "550e8400-e29b-41d4-a716-446655440002", name: "Linux-Server", type: "linux", status: "online", ip: "192.168.1.10" },
    { id: "550e8400-e29b-41d4-a716-446655440003", name: "NAS-01", type: "nas", status: "online", ip: "192.168.1.2" },
    { id: "550e8400-e29b-41d4-a716-446655440004", name: "OMV", type: "omv", status: "online", ip: "192.168.1.5" },
    { id: "550e8400-e29b-41d4-a716-446655440005", name: "PVE", type: "pve", status: "online", ip: "192.168.1.3" },
    { id: "550e8400-e29b-41d4-a716-446655440006", name: "PBS", type: "pbs", status: "offline", ip: "192.168.1.4" },
    { id: "550e8400-e29b-41d4-a716-446655440007", name: "Router", type: "router", status: "online", ip: "192.168.1.1" },
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

  // ─── Main Render ────────────────────────────────────────
  function renderDeviceRegistry() {
    var el = document.getElementById("devices");
    if (!el) return;

    var devices = MOCK_DEVICE_STORE;
    var cards = "";
    for (var i = 0; i < devices.length; i++) {
      var device = devices[i];
      var typeLabel = t("devices.type." + device.type) || device.type;

      cards += Components.renderCard({
        header:
          '<span class="device-card-name">' + esc(device.name) + "</span>" +
          Components.renderStatusBadge(device.status, "device"),
        body:
          '<div class="device-card-field"><span class="device-card-label">' + esc(t("devices.type")) + '</span><span class="device-card-value">' + esc(typeLabel) + "</span></div>" +
          '<div class="device-card-field"><span class="device-card-label">' + esc(t("devices.ip")) + '</span><span class="device-card-value">' + esc(device.ip || "-") + "</span></div>",
        dataAttributes: { "data-device-id": device.id }
      });
    }

    // Selector 选项
    var selectorOptions = [];
    for (var j = 0; j < MOCK_DEVICE_STORE.length; j++) {
      var d = MOCK_DEVICE_STORE[j];
      selectorOptions.push({ value: d.id, label: d.name + " (" + d.ip + ")" });
    }

    el.innerHTML =
      '<div class="band">' +
      '<div class="section-heading">' +
      "<div>" +
      '<h2>' + esc(t("registry.title")) + "</h2>" +
      '<p class="muted">' + esc(t("registry.subtitle")) + "</p>" +
      "</div>" +
      "</div>" +
      (devices.length
        ? '<div class="device-card-grid">' + cards + "</div>"
        : '<p class="muted">' + esc(t("registry.noDevice")) + "</p>") +
      "</div>" +
      '<div class="band top-gap">' +
      '<h3>' + esc(t("registry.selectorLabel")) + "</h3>" +
      Components.renderSelector({
        label: WorkOps.getLang() === "zh" ? "选择设备" : "Select Device",
        placeholder: WorkOps.getLang() === "zh" ? "-- 请选择设备 --" : "-- Select a device --",
        options: selectorOptions,
        selectedValue: "",
        onChange: ""
      }) +
      "</div>";
  }

  // ─── Public API ─────────────────────────────────────────
  window.DeviceRegistryModule = {
    render: renderDeviceRegistry,
    getDevices: function () { return MOCK_DEVICE_STORE; },
  };
})();
