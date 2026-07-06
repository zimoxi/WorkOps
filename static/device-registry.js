/**
 * WorkOps Device Registry — 设备注册中心
 * Sprint003: Device Registry Foundation
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

  // ─── StatusBadge Component ──────────────────────────────
  var STATUS_COLORS = {
    online: { bg: "#dcfce7", fg: "#15803d", label_zh: "在线", label_en: "Online" },
    offline: { bg: "#fee2e2", fg: "#b91c1c", label_zh: "离线", label_en: "Offline" },
    warning: { bg: "#fef3c7", fg: "#b45309", label_zh: "警告", label_en: "Warning" },
    unknown: { bg: "#f3f4f6", fg: "#647084", label_zh: "未知", label_en: "Unknown" },
  };

  function renderStatusBadge(status) {
    var s = STATUS_COLORS[status] || STATUS_COLORS.unknown;
    var isZh = WorkOps.getLang() === "zh";
    var label = isZh ? s.label_zh : s.label_en;
    return (
      '<span class="status-badge" style="background:' + s.bg + ";color:" + s.fg + '">' +
      "● " + esc(label) +
      "</span>"
    );
  }

  // ─── DeviceSelector Component ───────────────────────────
  function renderDeviceSelector(selectedId, onChangeFn) {
    var isZh = WorkOps.getLang() === "zh";
    var placeholder = isZh ? "-- 请选择设备 --" : "-- Select a device --";
    var label = isZh ? "选择设备" : "Select Device";

    var options = '<option value="">' + esc(placeholder) + "</option>";
    for (var i = 0; i < MOCK_DEVICE_STORE.length; i++) {
      var d = MOCK_DEVICE_STORE[i];
      var selected = d.id === selectedId ? " selected" : "";
      options += '<option value="' + esc(d.id) + '"' + selected + ">" + esc(d.name) + " (" + esc(d.ip) + ")</option>";
    }

    var onchange = onChangeFn ? ' onchange="' + esc(onChangeFn) + '(this.value)"' : "";
    return (
      '<div class="device-selector">' +
      '<label class="device-selector-label">' + esc(label) + "</label>" +
      '<select class="device-selector-select"' + onchange + ">" + options + "</select>" +
      "</div>"
    );
  }

  // ─── Device Card ────────────────────────────────────────
  function renderDeviceCard(device) {
    var typeLabel = t("devices.type." + device.type) || device.type;
    return (
      '<div class="device-card">' +
      '<div class="device-card-header">' +
      '<span class="device-card-name">' + esc(device.name) + "</span>" +
      renderStatusBadge(device.status) +
      "</div>" +
      '<div class="device-card-body">' +
      '<div class="device-card-field"><span class="device-card-label">' + esc(t("devices.type")) + '</span><span class="device-card-value">' + esc(typeLabel) + "</span></div>" +
      '<div class="device-card-field"><span class="device-card-label">' + esc(t("devices.ip")) + '</span><span class="device-card-value">' + esc(device.ip || "-") + "</span></div>" +
      "</div>" +
      "</div>"
    );
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
