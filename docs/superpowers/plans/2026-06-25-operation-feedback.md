# Operation Feedback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add visible status feedback and progress display for all important user actions.

**Architecture:** Preserve existing synchronous API behavior while adding optional async execution for UI-triggered command jobs. The frontend owns notifications, active job cards, polling, and output-based progress parsing.

**Tech Stack:** Python `ThreadingHTTPServer`, existing command catalog/executors, vanilla JavaScript, CSS, Python unittest, Node VM frontend tests.

---

### Task 1: Backend Async Jobs

**Files:**
- Modify: `backup_manager/server.py`
- Test: `tests/test_http_api.py`

- [ ] Add a failing test that posts `/api/run` with `async: true`, receives a `running` job, polls `/api/jobs/<id>`, and sees the final completed job.
- [ ] Implement an in-memory running job map on `AppContext`.
- [ ] Move command execution response assembly into a reusable helper.
- [ ] Start async jobs in a daemon thread only when `async: true` is present.
- [ ] Add `GET /api/jobs/<id>`.
- [ ] Run the targeted HTTP API test.

### Task 2: Frontend Feedback State

**Files:**
- Modify: `static/app.js`
- Modify: `static/styles.css`
- Test: `tests/test_frontend_operation_feedback.py`

- [ ] Add a failing Node VM test for `notify`, `renderOperationStatusRegion`, `extractProgress`, and active job cards.
- [ ] Add notification and active job fields to frontend state.
- [ ] Render a fixed operation status region into the page.
- [ ] Parse progress percentages from command output and fall back to indeterminate running progress.
- [ ] Run the targeted frontend test.

### Task 3: Wire Buttons

**Files:**
- Modify: `static/app.js`
- Test: `tests/test_frontend_operation_feedback.py`

- [ ] Add a failing test that `runOperation` sends `async: true` and records a running job.
- [ ] Update `runOperation` to show "preparing", "running", "success", and "failed" notifications.
- [ ] Poll `/api/jobs/<id>` until the returned job is no longer running.
- [ ] Add feedback around config saves, SSH tests, discovery, Windows preview, validation errors, and copy actions.
- [ ] Run the targeted frontend test.

### Task 4: Verification

**Files:**
- No new files.

- [ ] Run `py -m unittest tests.test_http_api -v`.
- [ ] Run `py -m unittest tests.test_frontend_operation_feedback -v`.
- [ ] Run `py -m unittest discover -s tests -v`.
- [ ] Run `node --check static/app.js`.
- [ ] Use a browser check on `http://127.0.0.1:8099/` to confirm the status region appears and does not overflow on desktop or mobile.
