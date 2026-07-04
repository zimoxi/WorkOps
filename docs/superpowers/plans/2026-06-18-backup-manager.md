# Backup Manager Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a generic web application for managing NAS/restic backups, dataset migration planning, Windows D/E backup guidance, cloud sync configuration, and optional PVE/PBS backup workflows.

**Architecture:** The first version is a dependency-light Python web app with a safe command catalog. It supports mock/local execution for Windows testing and leaves SSH execution as a controlled deployment mode for OMV/PVE.

**Tech Stack:** Python standard library HTTP server, unittest, JSON config, shell command adapters, Docker Compose for OMV deployment.

---

### Task 1: Core Models And Safety

**Files:**
- Create: `backup_manager/config.py`
- Create: `backup_manager/commands.py`
- Test: `tests/test_config.py`
- Test: `tests/test_commands.py`

- [ ] Define config dataclasses for storage targets, backup sets, restic repositories, cloud remotes, Windows backup, and PVE/PBS settings.
- [ ] Define a white-listed command catalog with operation metadata, instructions, danger level, and command builders.
- [ ] Reject unsafe restore targets such as `/tmp`, `/`, `/var`, and empty paths.
- [ ] Run `python -m unittest discover -s tests -v` and keep the new tests green.

### Task 2: Discovery Layer

**Files:**
- Create: `backup_manager/discovery.py`
- Test: `tests/test_discovery.py`

- [ ] Parse `zpool list`, `zfs list`, and `df -h` output into generic data objects.
- [ ] Provide folder discovery for a chosen mountpoint.
- [ ] Support mock discovery data for Windows local testing.
- [ ] Run `python -m unittest discover -s tests -v`.

### Task 3: Executors And Job History

**Files:**
- Create: `backup_manager/executor.py`
- Create: `backup_manager/jobs.py`

- [ ] Add mock executor for Windows testing.
- [ ] Add local executor for Linux/OMV.
- [ ] Add SSH command shape for later OMV/PVE deployment.
- [ ] Persist job history as JSON lines under `data/jobs.jsonl`.

### Task 4: Web UI

**Files:**
- Create: `backup_manager/server.py`
- Create: `static/styles.css`
- Create: `static/app.js`

- [ ] Implement dashboard, storage discovery, backup sets, restore assistant, migration assistant, Windows backup, cloud sync, and PVE/PBS pages.
- [ ] Add inline operation instructions on every page.
- [ ] Add danger modals for destructive or risky actions.
- [ ] Keep all command execution behind API endpoints that use the command catalog.

### Task 5: Packaging And Docs

**Files:**
- Create: `run.py`
- Create: `README.md`
- Create: `.env.example`
- Create: `docker/Dockerfile`
- Create: `docker-compose.yml`

- [ ] Provide Windows local run command.
- [ ] Provide OMV Docker Compose deployment command.
- [ ] Document safe mount/SSH options and why privileged Docker is not used.
- [ ] Run tests and start the local server for verification.
