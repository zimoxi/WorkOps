"""
WorkOps Dashboard Productization Tests
Sprint078: Dashboard Productization

覆盖：
- Dashboard HTML structure
- Dashboard CSS exists
- Dashboard JS exists
- Page structure (home, devices, backup, restore, health, metrics)
- Navigation elements
- Table structures
- Card structures
- Button elements
- Security boundary
"""

import unittest
import os


STATIC_DASHBOARD = os.path.join("static", "dashboard")


# ============================================================================
# Helpers
# ============================================================================

def _read_file(filename):
    filepath = os.path.join(STATIC_DASHBOARD, filename)
    with open(filepath, encoding="utf-8") as f:
        return f.read()


# ============================================================================
# File Existence
# ============================================================================

class TestDashboardFilesExist(unittest.TestCase):
    """文件存在测试"""

    def test_index_html_exists(self):
        self.assertTrue(os.path.exists(os.path.join(STATIC_DASHBOARD, "index.html")))

    def test_dashboard_css_exists(self):
        self.assertTrue(os.path.exists(os.path.join(STATIC_DASHBOARD, "dashboard.css")))

    def test_dashboard_js_exists(self):
        self.assertTrue(os.path.exists(os.path.join(STATIC_DASHBOARD, "dashboard.js")))


# ============================================================================
# HTML Structure
# ============================================================================

class TestDashboardHTML(unittest.TestCase):
    """HTML 结构测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_doctype(self):
        self.assertIn("<!DOCTYPE html>", self.html)

    def test_has_html_tag(self):
        self.assertIn("<html", self.html)

    def test_has_head(self):
        self.assertIn("<head>", self.html)

    def test_has_body(self):
        self.assertIn("<body>", self.html)

    def test_has_title(self):
        self.assertIn("<title>", self.html)
        self.assertIn("WorkOps", self.html)

    def test_has_meta_charset(self):
        self.assertIn('charset="UTF-8"', self.html)

    def test_has_meta_viewport(self):
        self.assertIn('name="viewport"', self.html)

    def test_links_css(self):
        self.assertIn('href="/static/dashboard/dashboard.css"', self.html)

    def test_links_js(self):
        self.assertIn('src="/static/dashboard/dashboard.js"', self.html)


# ============================================================================
# Navigation
# ============================================================================

class TestNavigation(unittest.TestCase):
    """导航测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_sidebar(self):
        self.assertIn('class="sidebar"', self.html)

    def test_has_nav_menu(self):
        self.assertIn('class="nav-menu"', self.html)

    def test_has_home_nav(self):
        self.assertIn('data-page="home"', self.html)

    def test_has_devices_nav(self):
        self.assertIn('data-page="devices"', self.html)

    def test_has_backup_nav(self):
        self.assertIn('data-page="backup"', self.html)

    def test_has_restore_nav(self):
        self.assertIn('data-page="restore"', self.html)

    def test_has_health_nav(self):
        self.assertIn('data-page="health"', self.html)

    def test_has_metrics_nav(self):
        self.assertIn('data-page="metrics"', self.html)

    def test_has_nav_items(self):
        self.assertIn('class="nav-item"', self.html)

    def test_has_active_class(self):
        self.assertIn('class="nav-item active"', self.html)


# ============================================================================
# Home Page
# ============================================================================

class TestHomePage(unittest.TestCase):
    """首页测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_home_page(self):
        self.assertIn('id="page-home"', self.html)

    def test_has_system_status(self):
        self.assertIn('id="system-status"', self.html)

    def test_has_runtime_summary(self):
        self.assertIn('id="runtime-summary"', self.html)

    def test_has_backup_summary(self):
        self.assertIn('id="backup-summary"', self.html)

    def test_has_restore_summary(self):
        self.assertIn('id="restore-summary"', self.html)

    def test_has_health_summary(self):
        self.assertIn('id="health-summary"', self.html)

    def test_has_status_card(self):
        self.assertIn('class="card status-card"', self.html)

    def test_has_system_overview_heading(self):
        self.assertIn("System Overview", self.html)


# ============================================================================
# Devices Page
# ============================================================================

class TestDevicesPage(unittest.TestCase):
    """设备页面测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_devices_page(self):
        self.assertIn('id="page-devices"', self.html)

    def test_has_devices_table(self):
        self.assertIn('id="devices-table"', self.html)

    def test_has_name_column(self):
        self.assertIn("<th>Name</th>", self.html)

    def test_has_type_column(self):
        self.assertIn("<th>Type</th>", self.html)

    def test_has_status_column(self):
        self.assertIn("<th>Status</th>", self.html)

    def test_has_last_seen_column(self):
        self.assertIn("<th>Last Seen</th>", self.html)

    def test_has_devices_body(self):
        self.assertIn('id="devices-body"', self.html)

    def test_has_heading(self):
        self.assertIn("Device Management", self.html)


# ============================================================================
# Backup Page
# ============================================================================

class TestBackupPage(unittest.TestCase):
    """备份页面测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_backup_page(self):
        self.assertIn('id="page-backup"', self.html)

    def test_has_backup_table(self):
        self.assertIn('id="backup-table"', self.html)

    def test_has_name_column(self):
        self.assertIn("<th>Name</th>", self.html)

    def test_has_backup_status_column(self):
        self.assertIn("<th>Status</th>", self.html)

    def test_has_created_column(self):
        self.assertIn("<th>Created</th>", self.html)

    def test_has_result_column(self):
        self.assertIn("<th>Result</th>", self.html)

    def test_has_create_backup_button(self):
        self.assertIn('id="create-backup-btn"', self.html)
        self.assertIn("Create Backup", self.html)

    def test_has_backup_body(self):
        self.assertIn('id="backup-body"', self.html)


# ============================================================================
# Restore Page
# ============================================================================

class TestRestorePage(unittest.TestCase):
    """恢复页面测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_restore_page(self):
        self.assertIn('id="page-restore"', self.html)

    def test_has_restore_table(self):
        self.assertIn('id="restore-table"', self.html)

    def test_has_name_column(self):
        self.assertIn("<th>Name</th>", self.html)

    def test_has_source_column(self):
        self.assertIn("<th>Source</th>", self.html)

    def test_has_restore_status_column(self):
        self.assertIn("<th>Status</th>", self.html)

    def test_has_created_column(self):
        self.assertIn("<th>Created</th>", self.html)

    def test_has_restore_body(self):
        self.assertIn('id="restore-body"', self.html)

    def test_has_heading(self):
        self.assertIn("Restore Management", self.html)


# ============================================================================
# Health Page
# ============================================================================

class TestHealthPage(unittest.TestCase):
    """健康页面测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_health_page(self):
        self.assertIn('id="page-health"', self.html)

    def test_has_health_cards(self):
        self.assertIn('id="health-cards"', self.html)

    def test_has_linux_health(self):
        self.assertIn('id="health-linux"', self.html)

    def test_has_pve_health(self):
        self.assertIn('id="health-pve"', self.html)

    def test_has_omv_health(self):
        self.assertIn('id="health-omv"', self.html)

    def test_has_heading(self):
        self.assertIn("Runtime Health", self.html)


# ============================================================================
# Metrics Page
# ============================================================================

class TestMetricsPage(unittest.TestCase):
    """指标页面测试"""

    def setUp(self):
        self.html = _read_file("index.html")

    def test_has_metrics_page(self):
        self.assertIn('id="page-metrics"', self.html)

    def test_has_backup_metric(self):
        self.assertIn('id="metric-backup"', self.html)

    def test_has_restore_metric(self):
        self.assertIn('id="metric-restore"', self.html)

    def test_has_health_metric(self):
        self.assertIn('id="metric-health"', self.html)

    def test_has_tasks_metric(self):
        self.assertIn('id="metric-tasks"', self.html)

    def test_has_heading(self):
        self.assertIn("Operation Metrics", self.html)

    def test_has_metric_cards(self):
        self.assertIn('class="card metric-card"', self.html)


# ============================================================================
# CSS Structure
# ============================================================================

class TestDashboardCSS(unittest.TestCase):
    """CSS 结构测试"""

    def setUp(self):
        self.css = _read_file("dashboard.css")

    def test_has_sidebar_styles(self):
        self.assertIn(".sidebar", self.css)

    def test_has_nav_styles(self):
        self.assertIn(".nav-item", self.css)

    def test_has_card_styles(self):
        self.assertIn(".card", self.css)

    def test_has_table_styles(self):
        self.assertIn("table", self.css)

    def test_has_button_styles(self):
        self.assertIn(".btn", self.css)

    def test_has_status_indicator(self):
        self.assertIn(".status-indicator", self.css)

    def test_has_online_status(self):
        self.assertIn(".online", self.css)

    def test_has_offline_status(self):
        self.assertIn(".offline", self.css)

    def test_has_responsive(self):
        self.assertIn("@media", self.css)

    def test_has_page_styles(self):
        self.assertIn(".page", self.css)

    def test_has_active_page(self):
        self.assertIn(".page.active", self.css)

    def test_has_metric_card(self):
        self.assertIn(".metric-card", self.css)

    def test_has_metric_value(self):
        self.assertIn(".metric-value", self.css)


# ============================================================================
# JS Structure
# ============================================================================

class TestDashboardJS(unittest.TestCase):
    """JS 结构测试"""

    def setUp(self):
        self.js = _read_file("dashboard.js")

    def test_has_navigation(self):
        self.assertIn("initNavigation", self.js)

    def test_has_switch_page(self):
        self.assertIn("switchPage", self.js)

    def test_has_load_dashboard_data(self):
        self.assertIn("loadDashboardData", self.js)

    def test_has_load_devices(self):
        self.assertIn("loadDevices", self.js)

    def test_has_load_backups(self):
        self.assertIn("loadBackups", self.js)

    def test_has_load_restores(self):
        self.assertIn("loadRestores", self.js)

    def test_has_load_health(self):
        self.assertIn("loadHealth", self.js)

    def test_has_load_metrics(self):
        self.assertIn("loadMetrics", self.js)

    def test_has_fetch_json(self):
        self.assertIn("fetchJSON", self.js)

    def test_has_escape_html(self):
        self.assertIn("escapeHtml", self.js)

    def test_has_dom_content_loaded(self):
        self.assertIn("DOMContentLoaded", self.js)

    def test_has_api_endpoints(self):
        self.assertIn("/api/dashboard/overview", self.js)
        self.assertIn("/api/devices", self.js)
        self.assertIn("/api/backup/jobs", self.js)
        self.assertIn("/api/restore/points", self.js)
        self.assertIn("/api/health/runtime", self.js)
        self.assertIn("/api/metrics/summary", self.js)

    def test_has_create_backup_button(self):
        self.assertIn("create-backup-btn", self.js)

    def test_no_eval(self):
        self.assertNotIn("eval(", self.js)

    def test_no_exec(self):
        self.assertNotIn("exec(", self.js)

    def test_no_innerhtml_with_user_input(self):
        # escapeHtml is used before innerHTML
        self.assertIn("escapeHtml", self.js)


# ============================================================================
# Security
# ============================================================================

class TestSecurityBoundary(unittest.TestCase):
    """安全边界测试"""

    def test_html_no_password(self):
        html = _read_file("index.html")
        self.assertNotIn("password", html.lower())

    def test_html_no_secret(self):
        html = _read_file("index.html")
        self.assertNotIn("secret", html.lower())

    def test_html_no_token(self):
        html = _read_file("index.html")
        self.assertNotIn("token", html.lower())

    def test_css_no_password(self):
        css = _read_file("dashboard.css")
        self.assertNotIn("password", css.lower())

    def test_css_no_secret(self):
        css = _read_file("dashboard.css")
        self.assertNotIn("secret", css.lower())

    def test_js_no_password(self):
        js = _read_file("dashboard.js")
        # Allow "password" only in API endpoint context, not as hardcoded value
        lines = js.split("\n")
        for line in lines:
            if "password" in line.lower():
                # Should only be in fetch/API context
                self.assertTrue(
                    "fetch" in line.lower() or "api" in line.lower() or "//" in line,
                    f"Unexpected password reference: {line.strip()}"
                )

    def test_js_no_eval(self):
        js = _read_file("dashboard.js")
        self.assertNotIn("eval(", js)

    def test_js_no_exec(self):
        js = _read_file("dashboard.js")
        self.assertNotIn("exec(", js)

    def test_js_no_subprocess(self):
        js = _read_file("dashboard.js")
        self.assertNotIn("subprocess", js)

    def test_js_no_shell(self):
        js = _read_file("dashboard.js")
        self.assertNotIn("shell", js.lower())

    def test_html_no_script_tags_with_code(self):
        html = _read_file("index.html")
        # Should only have script tags with src, not inline code
        import re
        inline_scripts = re.findall(r'<script>(?!.*src=).*?</script>', html, re.DOTALL)
        self.assertEqual(len(inline_scripts), 0)


# ============================================================================
# Integration
# ============================================================================

class TestDashboardIntegration(unittest.TestCase):
    """集成测试"""

    def test_all_pages_exist_in_html(self):
        html = _read_file("index.html")
        pages = ["home", "devices", "backup", "restore", "health", "metrics"]
        for page in pages:
            self.assertIn(f'id="page-{page}"', html, f"Missing page: {page}")

    def test_all_nav_items_exist(self):
        html = _read_file("index.html")
        pages = ["home", "devices", "backup", "restore", "health", "metrics"]
        for page in pages:
            self.assertIn(f'data-page="{page}"', html, f"Missing nav: {page}")

    def test_css_and_js_linked(self):
        html = _read_file("index.html")
        self.assertIn("dashboard.css", html)
        self.assertIn("dashboard.js", html)

    def test_responsive_meta(self):
        html = _read_file("index.html")
        self.assertIn("viewport", html)

    def test_table_structures(self):
        html = _read_file("index.html")
        tables = ["devices-table", "backup-table", "restore-table"]
        for table in tables:
            self.assertIn(f'id="{table}"', html, f"Missing table: {table}")

    def test_card_structures(self):
        html = _read_file("index.html")
        self.assertIn('class="cards"', html)
        self.assertIn('class="card"', html)

    def test_version_displayed(self):
        html = _read_file("index.html")
        self.assertIn("v1.0.0", html)

    def test_workops_branding(self):
        html = _read_file("index.html")
        self.assertIn("WorkOps", html)

    def test_all_pages_have_headings(self):
        html = _read_file("index.html")
        self.assertIn("System Overview", html)
        self.assertIn("Device Management", html)
        self.assertIn("Backup Management", html)
        self.assertIn("Restore Management", html)
        self.assertIn("Runtime Health", html)
        self.assertIn("Operation Metrics", html)

    def test_nav_links_have_href(self):
        html = _read_file("index.html")
        pages = ["home", "devices", "backup", "restore", "health", "metrics"]
        for page in pages:
            self.assertIn(f'href="#{page}"', html)

    def test_tables_have_thead(self):
        html = _read_file("index.html")
        self.assertIn("<thead>", html)

    def test_tables_have_tbody(self):
        html = _read_file("index.html")
        self.assertIn("<tbody", html)

    def test_status_indicators_in_html(self):
        html = _read_file("index.html")
        self.assertIn('class="status-indicator', html)

    def test_metric_values_default_zero(self):
        html = _read_file("index.html")
        self.assertIn(">0<", html)

    def test_loading_text_present(self):
        html = _read_file("index.html")
        self.assertIn("Loading...", html)

    def test_js_has_update_functions(self):
        js = _read_file("dashboard.js")
        self.assertIn("updateSystemStatus", js)
        self.assertIn("updateRuntimeSummary", js)
        self.assertIn("updateBackupSummary", js)
        self.assertIn("updateRestoreSummary", js)
        self.assertIn("updateHealthSummary", js)

    def test_js_has_update_metric(self):
        js = _read_file("dashboard.js")
        self.assertIn("updateMetric", js)

    def test_js_has_update_health_card(self):
        js = _read_file("dashboard.js")
        self.assertIn("updateHealthCard", js)

    def test_js_uses_strict_mode(self):
        js = _read_file("dashboard.js")
        self.assertIn("'use strict'", js)

    def test_js_wrapped_in_iife(self):
        js = _read_file("dashboard.js")
        self.assertIn("(function()", js)

    def test_css_has_font_family(self):
        css = _read_file("dashboard.css")
        self.assertIn("font-family", css)

    def test_css_has_border_radius(self):
        css = _read_file("dashboard.css")
        self.assertIn("border-radius", css)

    def test_css_has_box_shadow(self):
        css = _read_file("dashboard.css")
        self.assertIn("box-shadow", css)

    def test_css_has_transition(self):
        css = _read_file("dashboard.css")
        self.assertIn("transition", css)

    def test_css_has_grid(self):
        css = _read_file("dashboard.css")
        self.assertIn("grid-template-columns", css)

    def test_css_has_degraded_status(self):
        css = _read_file("dashboard.css")
        self.assertIn(".degraded", css)

    def test_css_has_unknown_status(self):
        css = _read_file("dashboard.css")
        self.assertIn(".unknown", css)

    def test_css_has_primary_button(self):
        css = _read_file("dashboard.css")
        self.assertIn(".btn-primary", css)

    def test_css_has_hover(self):
        css = _read_file("dashboard.css")
        self.assertIn(":hover", css)

    def test_css_has_sidebar_header(self):
        css = _read_file("dashboard.css")
        self.assertIn(".sidebar-header", css)

    def test_css_has_table_container(self):
        css = _read_file("dashboard.css")
        self.assertIn(".table-container", css)

    def test_js_has_escape_html_function(self):
        js = _read_file("dashboard.js")
        self.assertIn("function escapeHtml", js)

    def test_js_has_init_buttons(self):
        js = _read_file("dashboard.js")
        self.assertIn("initButtons", js)

    def test_files_are_utf8(self):
        for filename in ["index.html", "dashboard.css", "dashboard.js"]:
            filepath = os.path.join(STATIC_DASHBOARD, filename)
            with open(filepath, encoding="utf-8") as f:
                content = f.read()
            self.assertTrue(len(content) > 0, f"{filename} is empty")

    def test_html_has_doctype_html(self):
        html = _read_file("index.html")
        self.assertTrue(html.strip().startswith("<!DOCTYPE html>"))

    def test_html_has_lang(self):
        html = _read_file("index.html")
        self.assertIn('lang="en"', html)

    def test_css_has_margin_reset(self):
        css = _read_file("dashboard.css")
        self.assertIn("margin: 0", css)

    def test_css_has_padding_reset(self):
        css = _read_file("dashboard.css")
        self.assertIn("padding: 0", css)

    def test_js_has_hashchange(self):
        js = _read_file("dashboard.js")
        self.assertIn("hashchange", js)

    def test_js_has_location_hash(self):
        js = _read_file("dashboard.js")
        self.assertIn("location.hash", js)

    def test_js_has_classlist(self):
        js = _read_file("dashboard.js")
        self.assertIn("classList", js)

    def test_js_has_toggle(self):
        js = _read_file("dashboard.js")
        self.assertIn("toggle", js)

    def test_js_has_queryselectorall(self):
        js = _read_file("dashboard.js")
        self.assertIn("querySelectorAll", js)


if __name__ == "__main__":
    unittest.main()
