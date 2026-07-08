/**
 * WorkOps Auth Module — 认证模块
 * Sprint013: Authentication Foundation
 *
 * 只负责：
 * - Login UI
 * - User Badge
 * - currentUser 状态
 *
 * 禁止：
 * - MOCK_USER_STORE（后端私有）
 * - 权限判断
 * - 按钮隐藏
 *
 * 通过 window.AuthModule 暴露给 app.js。
 */
(function () {
  "use strict";

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

  // ─── Current User 状态 ──────────────────────────────────
  var currentUser = null;
  var loginError = "";

  // ─── API 调用 ───────────────────────────────────────────
  function apiLogin(username, password, callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/auth/login", true);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        try {
          var resp = JSON.parse(xhr.responseText);
          if (resp.success && resp.data && resp.data.user) {
            currentUser = resp.data.user;
            loginError = "";
            callback(true);
          } else {
            loginError = resp.error || t("auth.loginFailed");
            callback(false);
          }
        } catch (e) {
          loginError = t("auth.loginFailed");
          callback(false);
        }
      }
    };
    xhr.send(JSON.stringify({ username: username, password: password }));
  }

  function apiLogout(callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("POST", "/api/auth/logout", true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        currentUser = null;
        callback();
      }
    };
    xhr.send();
  }

  function apiMe(callback) {
    var xhr = new XMLHttpRequest();
    xhr.open("GET", "/api/auth/me", true);
    xhr.onreadystatechange = function () {
      if (xhr.readyState === 4) {
        try {
          var resp = JSON.parse(xhr.responseText);
          if (resp.success && resp.data && resp.data.user) {
            currentUser = resp.data.user;
            callback(true);
          } else {
            currentUser = null;
            callback(false);
          }
        } catch (e) {
          currentUser = null;
          callback(false);
        }
      }
    };
    xhr.send();
  }

  // ─── Login UI ───────────────────────────────────────────
  function renderLogin() {
    var el = document.getElementById("login-page");
    if (!el) return;

    var errorHtml = loginError
      ? '<div class="login-error">' + esc(loginError) + "</div>"
      : "";

    el.innerHTML =
      '<div class="login-container">' +
      '<div class="login-card">' +
      '<div class="login-header">' +
      '<h1 class="login-brand">' + esc(WorkOps.t("brand.name")) + "</h1>" +
      '<p class="login-tagline">' + esc(WorkOps.t("brand.tagline")) + "</p>" +
      "</div>" +
      '<form id="login-form" class="login-form">' +
      '<div class="login-field">' +
      '<label for="login-username">' + esc(t("auth.username")) + "</label>" +
      '<input type="text" id="login-username" name="username" autocomplete="username" placeholder="' + esc(t("auth.usernamePlaceholder")) + '" required />' +
      "</div>" +
      '<div class="login-field">' +
      '<label for="login-password">' + esc(t("auth.password")) + "</label>" +
      '<input type="password" id="login-password" name="password" autocomplete="current-password" placeholder="' + esc(t("auth.passwordPlaceholder")) + '" required />' +
      "</div>" +
      errorHtml +
      '<button type="submit" class="login-submit">' + esc(t("auth.login")) + "</button>" +
      "</form>" +
      "</div>" +
      "</div>";

    // 绑定表单提交
    var form = document.getElementById("login-form");
    if (form) {
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var username = document.getElementById("login-username").value.trim();
        var password = document.getElementById("login-password").value;
        if (!username || !password) {
          loginError = t("auth.fillAllFields");
          renderLogin();
          return;
        }
        apiLogin(username, password, function (success) {
          if (success) {
            // 登录成功，触发重渲染
            if (typeof render === "function") render();
          } else {
            renderLogin();
          }
        });
      });
    }
  }

  // ─── User Badge ─────────────────────────────────────────
  function renderUserBadge() {
    if (!currentUser) return "";

    var roleLabel = t("auth.role." + currentUser.role) || currentUser.role;

    return (
      '<div class="user-badge">' +
      '<span class="user-badge-name">' + esc(currentUser.username) + "</span>" +
      '<span class="user-badge-role role-' + esc(currentUser.role) + '">' + esc(roleLabel) + "</span>" +
      '<button class="user-badge-logout" onclick="AuthModule.logout()">' + esc(t("auth.logout")) + "</button>" +
      "</div>"
    );
  }

  // ─── Login / Logout ─────────────────────────────────────
  function login(username, password, callback) {
    apiLogin(username, password, callback);
  }

  function logout() {
    apiLogout(function () {
      // 登出后触发重渲染
      if (typeof render === "function") render();
    });
  }

  // ─── Current User ───────────────────────────────────────
  function getCurrentUser() {
    return currentUser;
  }

  function isLoggedIn() {
    return currentUser !== null;
  }

  // ─── 初始化（检查 Session）─────────────────────────────
  function init(callback) {
    apiMe(function (loggedIn) {
      if (callback) callback(loggedIn);
    });
  }

  // ─── Public API ─────────────────────────────────────────
  window.AuthModule = {
    renderLogin: renderLogin,
    renderUserBadge: renderUserBadge,
    login: login,
    logout: logout,
    getCurrentUser: getCurrentUser,
    isLoggedIn: isLoggedIn,
    init: init,
  };
})();
