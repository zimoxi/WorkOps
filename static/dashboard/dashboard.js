/**
 * WorkOps Dashboard JavaScript
 * Sprint078: Dashboard Productization
 */

(function() {
    'use strict';

    // Navigation
    function initNavigation() {
        const navItems = document.querySelectorAll('.nav-item');
        navItems.forEach(item => {
            item.addEventListener('click', function(e) {
                e.preventDefault();
                const page = this.dataset.page;
                switchPage(page);
            });
        });

        // Handle hash changes
        window.addEventListener('hashchange', function() {
            const page = window.location.hash.slice(1) || 'home';
            switchPage(page);
        });

        // Initial page
        const initialPage = window.location.hash.slice(1) || 'home';
        switchPage(initialPage);
    }

    function switchPage(pageName) {
        // Update navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === pageName);
        });

        // Update pages
        document.querySelectorAll('.page').forEach(page => {
            page.classList.toggle('active', page.id === 'page-' + pageName);
        });

        // Load page data
        loadPageData(pageName);
    }

    // Data loading
    function loadPageData(page) {
        switch(page) {
            case 'home':
                loadDashboardData();
                break;
            case 'devices':
                loadDevices();
                break;
            case 'backup':
                loadBackups();
                break;
            case 'restore':
                loadRestores();
                break;
            case 'health':
                loadHealth();
                break;
            case 'metrics':
                loadMetrics();
                break;
        }
    }

    async function fetchJSON(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) throw new Error('Network error');
            return await response.json();
        } catch (error) {
            console.error('Fetch error:', error);
            return null;
        }
    }

    // Dashboard
    async function loadDashboardData() {
        const data = await fetchJSON('/api/dashboard/overview');
        if (data) {
            updateSystemStatus(data.status);
            updateRuntimeSummary(data.runtimes);
            updateBackupSummary(data.backup);
            updateRestoreSummary(data.restore);
            updateHealthSummary(data.health);
        }
    }

    function updateSystemStatus(status) {
        const el = document.getElementById('system-status');
        if (el) {
            el.textContent = status || 'Online';
            el.className = 'status-indicator ' + (status || 'online').toLowerCase();
        }
    }

    function updateRuntimeSummary(runtimes) {
        const el = document.getElementById('runtime-summary');
        if (el && runtimes) {
            el.innerHTML = runtimes.map(r => 
                `<div>${r.name}: <span class="status-indicator ${r.status}">${r.status}</span></div>`
            ).join('');
        }
    }

    function updateBackupSummary(backup) {
        const el = document.getElementById('backup-summary');
        if (el && backup) {
            el.innerHTML = `
                <div>Total: ${backup.total || 0}</div>
                <div>Success: ${backup.successful || 0}</div>
                <div>Failed: ${backup.failed || 0}</div>
            `;
        }
    }

    function updateRestoreSummary(restore) {
        const el = document.getElementById('restore-summary');
        if (el && restore) {
            el.innerHTML = `
                <div>Total: ${restore.total || 0}</div>
                <div>Success: ${restore.successful || 0}</div>
                <div>Failed: ${restore.failed || 0}</div>
            `;
        }
    }

    function updateHealthSummary(health) {
        const el = document.getElementById('health-summary');
        if (el && health) {
            el.innerHTML = `
                <div>Healthy: ${health.healthy || 0}</div>
                <div>Warning: ${health.degraded || 0}</div>
                <div>Unavailable: ${health.unavailable || 0}</div>
            `;
        }
    }

    // Devices
    async function loadDevices() {
        const data = await fetchJSON('/api/devices');
        const tbody = document.getElementById('devices-body');
        if (tbody && data) {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No devices found</td></tr>';
            } else {
                tbody.innerHTML = data.map(d => `
                    <tr>
                        <td>${escapeHtml(d.display_name || d.name)}</td>
                        <td>${escapeHtml(d.device_type || d.type)}</td>
                        <td><span class="status-indicator ${(d.status || 'unknown').toLowerCase()}">${d.status || 'Unknown'}</span></td>
                        <td>${d.last_seen_at || d.last_seen || '-'}</td>
                    </tr>
                `).join('');
            }
        }
    }

    // Backups
    async function loadBackups() {
        const data = await fetchJSON('/api/backup/jobs');
        const tbody = document.getElementById('backup-body');
        if (tbody && data) {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No backup jobs</td></tr>';
            } else {
                tbody.innerHTML = data.map(b => `
                    <tr>
                        <td>${escapeHtml(b.name || b.backup_id)}</td>
                        <td><span class="status-indicator ${(b.status || 'unknown').toLowerCase()}">${b.status || 'Unknown'}</span></td>
                        <td>${b.created_at || b.created || '-'}</td>
                        <td>${escapeHtml(b.result || b.message || '-')}</td>
                    </tr>
                `).join('');
            }
        }
    }

    // Restores
    async function loadRestores() {
        const data = await fetchJSON('/api/restore/points');
        const tbody = document.getElementById('restore-body');
        if (tbody && data) {
            if (data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4">No restore points</td></tr>';
            } else {
                tbody.innerHTML = data.map(r => `
                    <tr>
                        <td>${escapeHtml(r.name || r.restore_id)}</td>
                        <td>${escapeHtml(r.source || r.backup_id || '-')}</td>
                        <td><span class="status-indicator ${(r.status || 'unknown').toLowerCase()}">${r.status || 'Unknown'}</span></td>
                        <td>${r.created_at || r.created || '-'}</td>
                    </tr>
                `).join('');
            }
        }
    }

    // Health
    async function loadHealth() {
        const data = await fetchJSON('/api/health/runtime');
        if (data) {
            updateHealthCard('health-linux', data.linux);
            updateHealthCard('health-pve', data.pve);
            updateHealthCard('health-omv', data.omv);
        }
    }

    function updateHealthCard(id, status) {
        const el = document.getElementById(id);
        if (el) {
            const state = (status || 'unknown').toLowerCase();
            el.textContent = status || 'Unknown';
            el.className = 'status-indicator ' + state;
        }
    }

    // Metrics
    async function loadMetrics() {
        const data = await fetchJSON('/api/metrics/summary');
        if (data) {
            updateMetric('metric-backup', data.backup_count);
            updateMetric('metric-restore', data.restore_count);
            updateMetric('metric-health', data.runtime_checks);
            updateMetric('metric-tasks', data.task_count);
        }
    }

    function updateMetric(id, value) {
        const el = document.getElementById(id);
        if (el) {
            el.textContent = value || 0;
        }
    }

    // Utility
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Create Backup button
    function initButtons() {
        const createBackupBtn = document.getElementById('create-backup-btn');
        if (createBackupBtn) {
            createBackupBtn.addEventListener('click', function() {
                alert('Create backup functionality - calls existing backup service boundary');
            });
        }
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', function() {
        initNavigation();
        initButtons();
        loadDashboardData();
    });

})();
