# Guided Workflow Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a ten-step guided workflow, automatic storage-target suggestions, field-level instructions, and reliable next-step navigation across every existing Backup Manager page.

**Architecture:** A new backend workflow module derives step status from saved configuration and job history. Discovery returns safe storage candidates without saving them. A small frontend workflow helper renders the shared step header, field guidance, progress checklist, skip controls, and next action while existing page functions retain ownership of their forms and operations.

**Tech Stack:** Python 3.11/3.12 standard library, vanilla JavaScript, CSS, `unittest`, existing HTTP server.

---

This directory is not a Git repository. Under `CODEX_GUARD.md`, implementation may write code but must not automatically run commands, tests, SSH, Docker, backup, restore, migration, or network operations. Every command below is a manual verification instruction for the operator.

## File Map

- Create `backup_manager/workflow.py`: workflow definitions and status derivation.
- Modify `backup_manager/config.py`: persist optional-step decisions without storing operational secrets.
- Modify `backup_manager/discovery.py`: generate safe storage-target candidates.
- Modify `backup_manager/server.py`: expose workflow status and skip/unskip endpoints.
- Create `static/workflow.js`: shared workflow UI and field-help components.
- Modify `static/app.js`: integrate overview, automatic form population, instructions, and next actions.
- Modify `static/styles.css`: progress, instruction, status, validation, and responsive styles.
- Modify `backup_manager/server.py` `INDEX_HTML`: load `workflow.js` before `app.js`.
- Create `tests/test_workflow.py`: workflow status tests.
- Modify `tests/test_discovery.py`: storage candidate tests.
- Modify `tests/test_http_api.py`: workflow endpoint tests.
- Modify `README.md`: explain the guided workflow and manual verification boundary.

### Task 1: Define Workflow State

**Files:**
- Modify: `backup_manager/config.py`
- Create: `backup_manager/workflow.py`
- Create: `tests/test_workflow.py`

- [ ] **Step 1: Write failing workflow-state tests**

```python
import unittest

from backup_manager.config import AppConfig, StorageTarget
from backup_manager.workflow import derive_workflow


class WorkflowTests(unittest.TestCase):
    def test_new_config_starts_at_connection(self):
        result = derive_workflow(AppConfig.default(), [])
        self.assertEqual(result["next_step"], "connect")
        self.assertEqual(result["steps"][0]["status"], "not_started")

    def test_active_storage_completes_storage_step(self):
        config = AppConfig(
            executor_mode="ssh",
            ssh_host="10.0.0.10",
            storage_targets=[
                StorageTarget("nas", "NAS", "zfs", "/data", "tank")
            ],
            active_storage_id="nas",
        )
        result = derive_workflow(config, [])
        storage = next(step for step in result["steps"] if step["id"] == "storage")
        self.assertEqual(storage["status"], "complete")

    def test_optional_step_can_be_skipped_and_reopened(self):
        config = AppConfig.from_dict(
            {"workflow": {"skipped_steps": {"dataset": "Not needed"}}}
        )
        result = derive_workflow(config, [])
        dataset = next(step for step in result["steps"] if step["id"] == "dataset")
        self.assertEqual(dataset["status"], "skipped")
```

- [ ] **Step 2: Manually run the test and confirm RED**

```powershell
py -m unittest tests.test_workflow -v
```

Expected: import failure because `backup_manager.workflow` does not exist.

- [ ] **Step 3: Add persisted workflow decisions**

Add to `backup_manager/config.py`:

```python
@dataclass
class WorkflowConfig:
    skipped_steps: dict[str, str] = field(default_factory=dict)
    completed_at: dict[str, str] = field(default_factory=dict)


class AppConfig:
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
```

Construct it in `from_dict()` with:

```python
workflow=WorkflowConfig(**data.get("workflow", {})),
```

- [ ] **Step 4: Implement workflow definitions and derivation**

`backup_manager/workflow.py` defines these IDs in this order:

```python
STEP_DEFINITIONS = (
    ("connect", "连接并发现", False),
    ("storage", "确认存储目标", False),
    ("dataset", "Dataset 规划与迁移", True),
    ("restic", "配置 NAS / Restic", False),
    ("first_backup", "首次备份", False),
    ("restore_verify", "恢复验证", False),
    ("schedule", "自动计划与通知", False),
    ("windows", "Windows 备份", True),
    ("cloud", "云端异地备份", True),
    ("pve_pbs", "PVE / PBS", True),
)
```

Use pure helper functions to derive status. Successful jobs are records where `status == "success"` and `operation_id` matches:

```python
first_backup -> restic-backup
restore_verify -> restic-restore
cloud -> cloud-rclone-sync
pve_pbs -> pve-vzdump
```

Connection completes only when both `workflow.completed_at["ssh_test"]` and `workflow.completed_at["storage_discovery"]` exist; storage completes from `active_storage()`; Restic completes when repository, password file, and included paths exist. A skipped optional step overrides `not_started` but never overrides a successful completion.

- [ ] **Step 5: Manually verify workflow tests**

```powershell
py -m unittest tests.test_workflow -v
```

Expected: all workflow tests pass.

### Task 2: Suggest Safe Storage Targets

**Files:**
- Modify: `backup_manager/discovery.py`
- Modify: `backup_manager/server.py`
- Modify: `tests/test_discovery.py`

- [ ] **Step 1: Write failing candidate-filter tests**

```python
def test_suggest_storage_targets_excludes_system_and_unmounted_datasets(self):
    datasets = [
        {"name": "rpool/ROOT", "mountpoint": "/", "used": "8G", "avail": "20G"},
        {"name": "tank", "mountpoint": "/tank", "used": "2T", "avail": "8T"},
        {"name": "tank/legacy", "mountpoint": "legacy", "used": "1G", "avail": "8T"},
    ]
    result = suggest_storage_targets(datasets)
    self.assertEqual(result, [{
        "id": "discovered-tank",
        "name": "tank",
        "kind": "zfs",
        "pool_name": "tank",
        "mountpoint": "/tank",
        "notes": "自动发现，保存前请确认",
    }])
```

- [ ] **Step 2: Manually run the focused test and confirm RED**

```powershell
py -m unittest tests.test_discovery.DiscoveryParsingTests.test_suggest_storage_targets_excludes_system_and_unmounted_datasets -v
```

Expected: import failure for `suggest_storage_targets`.

- [ ] **Step 3: Implement candidate filtering**

Add `suggest_storage_targets(datasets)` to `discovery.py`. Reject empty mountpoints, `/`, `legacy`, `none`, `-`, and non-absolute paths. Derive the pool name from the dataset name before the first `/`. Generate deterministic IDs by replacing `/` with `-`.

- [ ] **Step 4: Return candidates from discovery**

Add to `discover_storage()` output:

```python
"storage_candidates": suggest_storage_targets(parse_zfs_list(datasets_output)),
```

Mock discovery returns one matching candidate for `ExamplePool`.

- [ ] **Step 5: Manually verify discovery tests**

```powershell
py -m unittest tests.test_discovery tests.test_server -v
```

Expected: candidate filtering and existing discovery behavior pass.

### Task 3: Expose Workflow Status And Skip Decisions

**Files:**
- Modify: `backup_manager/server.py`
- Modify: `tests/test_http_api.py`

- [ ] **Step 1: Write failing HTTP tests**

```python
def test_state_includes_workflow(self):
    status, payload = get_json(server.base_url, "/api/state")
    self.assertEqual(status, 200)
    self.assertIn("workflow", payload)
    self.assertEqual(payload["workflow"]["next_step"], "connect")

def test_optional_step_can_be_skipped_and_reopened(self):
    status, payload = post_json(server.base_url, "/api/workflow/step", {
        "step_id": "windows", "action": "skip", "reason": "No Windows PC"
    })
    self.assertEqual(status, 200)
    self.assertEqual(payload["step"]["status"], "skipped")

    status, payload = post_json(server.base_url, "/api/workflow/step", {
        "step_id": "windows", "action": "reopen"
    })
    self.assertEqual(payload["step"]["status"], "not_started")
```

- [ ] **Step 2: Manually confirm the endpoint tests fail**

```powershell
py -m unittest tests.test_http_api.HttpApiTests.test_state_includes_workflow tests.test_http_api.HttpApiTests.test_optional_step_can_be_skipped_and_reopened -v
```

Expected: missing workflow response and 404 endpoint.

- [ ] **Step 3: Add workflow to state payload**

In `json_response_payload()` call:

```python
workflow = derive_workflow(config, context.job_store.latest())
```

Return it under the `workflow` key.

- [ ] **Step 4: Add skip/reopen endpoint**

Allow actions only for `dataset`, `windows`, `cloud`, and `pve_pbs`. `skip` requires a non-empty reason under 200 characters. `reopen` deletes the saved skip reason. Save through `ConfigStore`; return the updated step and workflow.

On successful `/api/test-ssh`, save `workflow.completed_at["ssh_test"] = now_iso()`. After discovery completes with at least one parsed pool or dataset and no connection-level error, save `workflow.completed_at["storage_discovery"] = now_iso()`. Do not mark either item from a failed or partial connection result.

- [ ] **Step 5: Manually verify HTTP tests**

```powershell
py -m unittest tests.test_http_api -v
```

Expected: state, skip/reopen, password-redaction, and discovery tests pass.

### Task 4: Build Shared Workflow UI Components

**Files:**
- Create: `static/workflow.js`
- Modify: `backup_manager/server.py` (`INDEX_HTML`)
- Modify: `static/styles.css`
- Modify: `static/app.js`

- [ ] **Step 1: Add shared workflow helpers**

Create `window.BackupWorkflow` with:

```javascript
window.BackupWorkflow = {
  renderOverview(workflow, onOpen),
  renderStepHeader(stepId, workflow),
  renderFieldHelp({ purpose, example, format, safety }),
  renderStepFooter(stepId, workflow),
  statusLabel(status),
};
```

The overview renders ten stable rows, status text plus icon, one recommended-next marker, progress count, and a primary `继续` action. It does not nest cards inside cards.

- [ ] **Step 2: Load helper before the application**

Change `INDEX_HTML` scripts to:

```html
<script src="/static/workflow.js"></script>
<script src="/static/app.js"></script>
```

- [ ] **Step 3: Store workflow state in the frontend**

Initialize:

```javascript
const state = {
  config: null,
  discovery: null,
  jobs: [],
  workflow: null,
  sshPassword: "",
  connectionResult: null,
};
```

Set `state.workflow = payload.workflow` in `init()` and after configuration, skip, job, and discovery actions.

- [ ] **Step 4: Replace the overview hero with the workflow checklist**

Keep compact storage and repository summary metrics below the checklist. The first viewport must show current progress, the recommended next step, and enough of the following section to indicate more content.

- [ ] **Step 5: Add responsive workflow styles**

Use stable columns for status, number, title, and action at desktop width; stack title and action at mobile width. Status must use icon plus text, not color alone. Cards retain the existing 8px maximum radius.

- [ ] **Step 6: Manually validate JavaScript syntax**

```powershell
node --check static/workflow.js
node --check static/app.js
```

Expected: both checks exit 0.

### Task 5: Automatically Fill Storage Target Forms

**Files:**
- Modify: `static/app.js`
- Modify: `static/styles.css`

- [ ] **Step 1: Render candidate actions**

In `renderDiscovery()`, add a storage-target section before Pool. If several candidates exist, render one `设为存储目标` button per candidate. `renderDiscovery()` only returns markup; it does not touch form elements before they exist.

- [ ] **Step 2: Implement form population without saving**

```javascript
function populateStorageCandidate(candidate) {
  $("#storageName").value = candidate.name;
  $("#storageKind").value = candidate.kind;
  $("#storagePool").value = candidate.pool_name;
  $("#storageMount").value = candidate.mountpoint;
  $("#storageSuggestion").textContent = "已自动填写，请确认后添加。";
}
```

At the end of `renderStorage()`, after assigning `innerHTML`, call `applyAutomaticStorageSuggestion()`. That function auto-populates only when there is exactly one candidate, no active storage target, and all four target inputs are still empty. Do not call `/api/config` from either function.

- [ ] **Step 3: Add inline field instructions**

Storage name explains that it is a display label. Pool name shows `Gensol` only as an example, never as a default. Mountpoint explains that it must be an absolute data path and must not be `/`, `/tmp`, or a system directory.

- [ ] **Step 4: Continue after confirmation**

After `addStorageTarget()` saves the target, call `discover()` again with the current request-scoped SSH password. The backend can then run folder discovery against the newly active mountpoint. Display those folders and set the next action to Dataset planning. Do not make Dataset migration mandatory.

### Task 6: Add Step Headers And Field Help To Every Menu

**Files:**
- Modify: `static/app.js`
- Modify: `static/styles.css`

- [ ] **Step 1: Storage page**

Add purpose, prerequisites, host/user/port/auth examples, host-key safety, connection success criteria, automatic-target explanation, and next action.

- [ ] **Step 2: Dataset migration page**

Explain that migration belongs before long-term backup setup and is usually one-time. Add field examples for mountpoint, temporary directory name, old directory, dataset name, and destination mountpoint. Show the ten migration stages from the design spec and keep destructive confirmation.

- [ ] **Step 3: NAS/Restic page**

Explain repository, password file, included paths, exclusions, tag, and retention. Every multiline input says `每行一条`. Show current source-to-repository preview, same-pool limitation warning, first-backup success criteria, and restore-verification next action.

- [ ] **Step 4: Windows page**

Replace comma-separated drive help with one path per line examples:

```text
D:\
E:\
D:\Finance
E:\Photos\Originals
```

Explain whole-drive versus folder backup, no-quote rule, UNC target syntax, mirror deletion risk, and source-to-destination preview. This task changes instructions and preview only; the separate Windows data-model plan implements arbitrary source-path persistence and collision handling.

- [ ] **Step 5: Cloud page**

Explain provider choice, rclone remote syntax, encrypted repository source, capacity, authorization ownership, and first-sync verification. Make the same-pool versus offsite distinction explicit.

- [ ] **Step 6: PVE/PBS page**

Explain that this is a separate optional PVE-host workflow. Add examples for PVE host, PBS storage ID, target PVE version, VM/CT ID, backup mode, and restore-drill success criteria.

- [ ] **Step 7: Job page**

Group jobs by workflow step, show the latest job first, and add a `返回此步骤` action. Keep command output collapsed by default and preserve secret redaction.

### Task 7: Add Skip And Next-Step Interactions

**Files:**
- Modify: `static/app.js`

- [ ] **Step 1: Implement optional-step skipping**

Use a small dialog requiring a reason. POST:

```javascript
{
  step_id: stepId,
  action: "skip",
  reason: reason.trim(),
}
```

Do not reuse the destructive-operation dialog because skipping is reversible and not dangerous.

- [ ] **Step 2: Implement reopen**

Skipped steps display `重新启用`; POST `{step_id, action: "reopen"}` and refresh workflow state.

- [ ] **Step 3: Implement continue navigation**

Map workflow IDs to existing pages:

```javascript
const STEP_PAGES = {
  connect: "storage",
  storage: "storage",
  dataset: "migration",
  restic: "nas",
  first_backup: "nas",
  restore_verify: "nas",
  schedule: "nas",
  windows: "windows",
  cloud: "cloud",
  pve_pbs: "pve",
};
```

After successful actions, update state from `/api/state` and navigate only when the user clicks `继续下一步`.

### Task 8: Verification And Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document the ten-step workflow**

Explain required versus optional steps, automatic status, skip/reopen, automatic storage suggestions, and field-level examples.

- [ ] **Step 2: Manually run the complete test suite**

```powershell
py -m unittest discover -s tests -v
py -m compileall -f backup_manager run.py
node --check static/workflow.js
node --check static/app.js
```

Expected: all tests and syntax checks pass.

- [ ] **Step 3: Manual browser verification**

At 1440x900 and 390x844, verify the overview checklist, status text, automatic target form fill, candidate selection, every field-help block, skip/reopen dialog, next-step navigation, collapsed logs, and absence of horizontal overflow.

- [ ] **Step 4: Preserve the execution boundary**

Use mock executor and fixture discovery only. Do not run SSH, Docker, Restic, rclone, rsync, ZFS, vzdump, backup, restore, migration, or network commands during automated verification.

## Follow-On Plans

After this foundation is complete, create two separate implementation plans:

1. `Core Data Protection`: full Dataset migration stages, Restic initialization, first-backup progress, restore-drill records, schedules, and email notifications.
2. `Optional Protection Sources`: arbitrary Windows source paths and collision-safe destinations, cloud provider onboarding and verification, PVE/PBS readiness and restore drills, and workflow-grouped job reporting enhancements.
