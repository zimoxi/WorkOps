/**
 * WorkOps Device Registry — 设备注册中心
 * Sprint003: Device Registry Foundation
 * Sprint007: 迁移到 Components（兼容层保留）
 *
 * 独立模块，不依赖后端 API。
 * 通过 window.DeviceRegistryModule 暴露给 app.js。
 */
(function () {
  "use strict";

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

  // ─── 兼容层：StatusBadge（转调 Components）──────────────
  // 旧函数保留，内部转调 Components
  // Sprint008 将删除此兼容层
  function renderStatusBadge(status) {
    if (window.Components && Components.renderStatusBadge) {
      return Components.renderStatusBadge(status, "device");
    }
    // 降级方案（Components 未加载时）
    return '<span class="status-badge">● ' + esc(status) + "</span>";
  }

  // ─── 兼容层：DeviceSelector（转调 Components）───────────
  // 旧函数保留，内部转调 Components
  // Sprint008 将删除此兼容层
  function renderDeviceSelector(selectedId, onChangeFn) {
    if (window.Components && Components.renderSelector) {
      var isZh = WorkOps.getLang() === "zh";
      var placeholder = isZh ? "-- 请选择设备 --" : "-- Select a device --";
      var label = isZh ? "选择设备" : "Select Device";

      var options = [];
      for (var i = 0; i < MOCK_DEVICE_STORE.length; i++) {
        var d = MOCK_DEVICE_STORE[i];
        options.push({ value: d.id, label: d.name + " (" + d.ip + ")" });
      }

      return Components.renderSelector({
        label: label,
        placeholder: placeholder,
        options: options,
        selectedValue: selectedId,
        onChange: onChangeFn
      });
    }
    // 降级方案
    return '<div class="device-selector">Selector unavailable</div>';
  }

  // ─── 兼容层：DeviceCard（转调 Components）────────────────
  // 旧函数保留，内部转调 Components
  // Sprint008 将删除此兼容层
  function renderDeviceCard(device) {
    if (window.Components && Components.renderCard) {
      var typeLabel = t("devices.type." + device.type) || device.type;

      var header =
        '<span class="device-card-name">' + esc(device.name) + "</span>" +
        renderStatusBadge(device.status);

      var body =
        '<div class="device-card-field"><span class="device-card-label">' + esc(t("devices.type")) + '</span><span class="device-card-value">' + esc(typeLabel) + "</span></div>" +
        '<div class="device-card-field"><span class="device-card-label">' + esc(t("devices.ip")) + '</span><span class="device-card-value">' + esc(device.ip || "-") + "</span></div>";

      return Components.renderCard({
        header: header,
        body: body,
        dataAttributes: { "data-device-id": device.id }
      });
    }
    // 降级方案
    return '<div class="device-card">Card unavailable</div>';
  }

  // ─── Main Render ────────────────────────────────────────
  function renderDeviceRegistry() {
    var el = document.getElementById("devices");
    if (!el) return;

    var devices = MOCK_DEVICE_STORE;
    var cards = "";
    for (var i = 0; i < devices.length; i++) {
      cards += renderDeviceCard(devices[i]);
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
      renderDeviceSelector("", "") +
      "</div>";
  }

  // ─── Public API ─────────────────────────────────────────
  window.DeviceRegistryModule = {
    render: renderDeviceRegistry,
    renderStatusBadge: renderStatusBadge,
    renderDeviceSelector: renderDeviceSelector,
    getDevices: function () { return MOCK_DEVICE_STORE; },
  };
})();
