# Cloud Provider Guides Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe, provider-specific OneDrive and Google Drive onboarding to the existing cloud backup wizard.

**Architecture:** Extend the declarative `CLOUD_GUIDES` data and make command generation understand interactive OAuth guides. Reuse the existing render path and cloud operations so no backend protocol or dependency changes are required.

**Tech Stack:** Vanilla JavaScript, CSS, Python `unittest`, Node.js VM test harness

---

### Task 1: Specify OAuth Guide Behavior

**Files:**
- Modify: `tests/test_frontend_cloud.py`
- Test: `tests/test_frontend_cloud.py`

- [ ] Add assertions that `microsoft-onedrive` and `google-drive` guides exist, use OAuth, contain no password fields, and generate `rclone config`.
- [ ] Run `py -m unittest tests.test_frontend_cloud -v` and confirm failure because the guides do not exist.

### Task 2: Implement Provider Guides

**Files:**
- Modify: `static/app.js`
- Modify: `static/styles.css`

- [ ] Add declarative OneDrive and Google Drive guide entries with official source links, OAuth warnings, and provider-specific recovery notes.
- [ ] Update `defaultCloudGuideId` and `cloudCreateCommand` so persisted OAuth providers select the correct guide and preview interactive configuration safely.
- [ ] Render authentication type, success criterion, and troubleshooting information using the existing 8px visual system.
- [ ] Run `py -m unittest tests.test_frontend_cloud -v` and confirm it passes.

### Task 3: Verify Integration

**Files:**
- Verify: `static/app.js`
- Verify: `static/styles.css`

- [ ] Run `node --check static/app.js` and expect exit code 0.
- [ ] Run `py -m unittest discover -s tests -v` and expect all tests to pass.
- [ ] Open `http://127.0.0.1:8099`, switch between Baidu, OneDrive, and Google Drive, and verify desktop/mobile layout, dynamic instructions, and command previews.
