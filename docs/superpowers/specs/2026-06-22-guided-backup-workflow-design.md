# Guided Backup Control Center Design

## Goal

Turn Backup Manager from a collection of independent utilities into a guided backup and restore control center.

A first-time user must always understand:

- what system is currently being managed;
- which backup and restore features are actually available on that system;
- what existing tasks, repositories, backups, and restore leftovers have already been discovered;
- what the safest next step is;
- how to recover data without relying on shell memory.

The application remains a manual-operations product under `CODEX_GUARD.md`. It may discover, explain, preview, and orchestrate actions, but it must not silently trust or silently delete.

## Scope

First release scope:

- OMV over SSH;
- PVE over SSH;
- generic Linux over SSH;
- the current local Windows machine where the application is running.

This release does not support remote Windows management. It also does not attempt to deeply integrate with vendor-specific NAS platforms such as TrueNAS, Unraid, Synology, or QNAP.

## Core Product Model

The product is no longer OMV-specific. It becomes a host-aware control center built around three layers:

1. `platform_profile`: what kind of host this is.
2. `capability_profile`: what backup-related features are available on that host.
3. `inventory`: what storage, repositories, snapshots, schedules, restore tasks, and leftovers already exist.

The UI only exposes workflows and actions supported by the current profiles and inventory.

## Platform Detection

The application automatically probes the target and classifies it as one of:

- `windows-local`
- `pve`
- `omv`
- `linux`

Recommended detection order:

1. If the app is running locally on Windows, classify as `windows-local`.
2. If the remote host exposes `pveversion`, `qm`, `pct`, and `pvesm`, classify as `pve`.
3. If the remote host exposes OpenMediaVault package, config, or command signatures, classify as `omv`.
4. Otherwise classify as generic `linux`.

The user may correct a wrong classification in the UI, but auto-detection remains the default path.

## Capability Detection

Capability detection is independent from platform detection. A platform label never implies a capability unless it is directly verified.

Capabilities include:

- `zfs`
- `restic`
- `rclone`
- `systemd`
- `cron`
- `pbs`
- `smb`

Examples:

- an OMV host may have `zfs` and `systemd` but not `restic`;
- a generic Linux host may have `zfs`, `restic`, and `rclone`;
- a PVE host may expose `pbs` support even when the selected OMV VM does not.

## Navigation Model

The overview becomes a host-aware checklist rather than a static tool dashboard.

Base workflow:

1. Connect and identify the host.
2. Confirm the active storage target.
3. Configure the restore staging root.
4. Plan or skip Dataset migration.
5. Configure NAS and Restic.
6. Run the first backup.
7. Use the restore center for verification or recovery.
8. Configure schedules and notifications.
9. Configure or skip Windows local backup.
10. Configure or skip cloud offsite replication.
11. Configure or skip PVE/PBS backup.

Rules:

- required steps remain ordered;
- optional steps can be skipped and reopened later;
- unsupported steps are hidden or marked unavailable based on capability detection;
- advanced users may still open later pages directly from the sidebar;
- every page shows the recommended next step and its completion criteria.

Examples:

- on a non-ZFS Linux host, Dataset migration is hidden and restore staging falls back to a normal directory root;
- on local Windows, ZFS and PBS pages are hidden, while Windows backup is active;
- on PVE, the PVE/PBS branch is shown only when PBS-related capability checks pass.

## Step Status

Each workflow step has one of these states:

- `not_started`
- `needs_attention`
- `complete`
- `skipped`
- `unavailable`

Completion is derived from real configuration and evidence whenever possible.

- Connect and identify: latest connection test succeeded and the platform profile is known.
- Storage target: an active storage target is confirmed.
- Restore staging root: a safe restore root exists and has been validated.
- Dataset migration: migration completed or the step was explicitly skipped.
- NAS and Restic: repository, password file, and at least one included path are configured.
- First backup: a successful Restic snapshot or equivalent backup artifact exists.
- Restore center: at least one restore verification task completed successfully.
- Schedules: required backup and verification schedules are discovered or configured.
- Windows backup: at least one Windows source and a destination are configured, or the step is skipped.
- Cloud: an rclone remote and upload target are verified, or the step is skipped.
- PVE/PBS: a PBS target and restore drill evidence exist, or the step is skipped.

The overview shows progress, attention states, the next actionable step, and whether stale or duplicate tasks were found.

## Inventory Model

The backend collects a normalized inventory from the current host and configuration.

The inventory includes:

- platform profile;
- capability profile;
- pools, datasets, mountpoints, and first-level folders;
- active storage candidates;
- Restic repositories and snapshots when discoverable;
- schedule entries from OMV, systemd, or cron when discoverable;
- PVE guests, PBS stores, and recent backup evidence when discoverable;
- Windows local drives when running on Windows;
- restore tasks and staging directories;
- warnings such as duplicate schedules, stale staging directories, or unsupported paths.

The UI must distinguish three origins for discovered objects:

- `app_managed`
- `system_existing`
- `externally_discovered`

The application shows facts only. If an object cannot be safely validated, it is labeled as discovered but unverified instead of being marked successful.

## Storage Discovery And Confirmation

Storage discovery remains generic and must not hard-code pool names.

After discovery:

- unsafe mountpoints such as `/`, `/tmp`, `/var`, `/etc`, `/root`, `/usr`, and `/boot` are excluded from storage suggestions;
- if exactly one suitable dataset exists, its values pre-fill the storage form but are not auto-saved;
- if multiple suitable datasets exist, each row provides a `Use as storage target` action;
- the user must still explicitly confirm and save the target.

The page must also explain what a valid storage target means:

- it is the main data location whose folders will be backed up;
- it is not the system disk root;
- it is where first-level folders are enumerated for Restic selection and Dataset migration planning.

## Restore Staging Root

Restore operations must not default to `/tmp`, `/`, or other small or system-owned paths.

On ZFS-capable hosts, the preferred model is a dedicated parent dataset:

- dataset name example: `Gensol/backup-manager-restore`
- mountpoint example: `/Gensol/.backup-manager/restore`

The application:

- detects whether this parent dataset already exists;
- verifies mountpoint, free space, and write access;
- warns if the path is still included in backup sources;
- offers a guided create action with impact and rollback notes.

On hosts without ZFS, the restore staging root falls back to a normal directory under a safe data path. The UI must clearly label this as a lower-isolation mode.

## Dataset Migration

Dataset migration remains optional. It is only needed when a user wants independent ZFS properties, snapshots, quotas, or ownership boundaries for specific folders.

Migration continues to be a one-time guided assistant with explicit stages:

1. detect whether the source is already a dataset;
2. verify source size and available space;
3. create a temporary migration directory on the same pool;
4. explain which SMB share or application write path must be paused;
5. move the old directory aside;
6. create the new dataset with the intended mountpoint;
7. copy data with ownership, ACL, xattr, hard link, and timestamp preservation;
8. compare size, file count, permissions, and sampled hashes;
9. restore share access;
10. retain the old directory until a separate destructive confirmation.

Every destructive sub-step requires typed confirmation and a visible rollback path.

## NAS And Restic

NAS and Restic remain split into setup, first backup, and restore usage so the user can see exactly what is incomplete.

Setup covers:

- repository path;
- password file path;
- included folders;
- exclusions;
- tag;
- retention policy.

Folder selection comes from the confirmed storage target. The page must detect whether the repository already exists before offering initialization.

The setup page also explains a critical limitation:

- a Restic repository stored on the same pool is still useful against accidental deletion and ransomware cleanup workflows;
- it is not a complete independent backup until it is copied to an external disk, another machine, or cloud storage.

## First Backup

The first-backup page shows:

- exact source folders;
- exclusion rules;
- destination repository;
- expected scan behavior;
- progress location;
- what success looks like;
- the required next step: open the restore center and complete a restore verification task.

Once a successful snapshot exists, the workflow unlocks the restore center step.

## Restore Center

The restore center becomes a first-class module instead of a one-off command form.

It supports three restore modes:

1. restore verification to staging only;
2. restore to a new target location;
3. restore to the original location through a guarded overwrite flow.

Default behavior:

- restore always goes to staging first;
- direct overwrite is not the default path;
- auto-cleanup is off by default.

### Restore Task Lifecycle

Every restore creates a task record with:

- restore task ID;
- source backup object or snapshot ID;
- selected restore paths;
- staging directory name;
- staging directory full path;
- target path, if any;
- creation time;
- current status;
- origin marker.

Suggested statuses:

- `created`
- `restoring`
- `restored_pending_review`
- `reviewed`
- `copied_to_new_target`
- `overwritten_to_original`
- `cleanup_pending`
- `cleaned`
- `failed`
- `interrupted`

### Staging Directory Layout

Recommended ZFS model:

- one dedicated parent dataset for restores;
- one subdirectory per restore task under that parent dataset.

Example:

- parent dataset: `Gensol/backup-manager-restore`
- parent mountpoint: `/Gensol/.backup-manager/restore`
- per-task path: `/Gensol/.backup-manager/restore/restore-20260623-153000`

This is preferred over creating one new dataset per restore task because it keeps cleanup simpler while still isolating restore data from the system disk.

### Staging Directory Lists

The restore center shows two separate lists:

1. application-created staging directories;
2. other directories discovered under the restore root.

Each row shows:

- whether files currently exist;
- directory name;
- full path;
- related restore task, when known;
- source snapshot, when known;
- creation time, when known;
- current status;
- whether the directory is app-managed or external.

Delete behavior:

- app-managed directories may be deleted through a guarded confirmation flow;
- external directories may also be deleted, but require stronger confirmation text such as `DELETE <directory-name>`;
- deletion is only allowed inside the restore parent dataset or configured restore root.

### Verification And Promotion

After a restore completes, the user can:

- keep the staging directory;
- copy the restored data to a new location;
- overwrite the original location through an advanced guarded flow.

Overwrite protection requires:

- explicit risk explanation;
- source path and target path preview;
- visible list or estimate of impacted files;
- typed confirmation text such as `OVERWRITE /target/path`.

Default overwrite behavior replaces same-name files but does not delete target-only files. Destructive mirror-style restore, if added later, must be a separate danger mode.

### Cleanup Rules

Cleanup is intentionally conservative:

- staging directories are not deleted automatically after restore;
- cleanup becomes available only after user review and a subsequent copy or overwrite step;
- failed, interrupted, or unverified restores must retain their staging data;
- an optional `cleanup after confirmed promotion` toggle may exist, but only after successful review.

## Existing Backup, Restore, And Task Lists

The application exposes four main list views:

1. backup task list;
2. backup artifact list;
3. restore task list;
4. staging directory list.

### Backup Task List

Each task row shows:

- name;
- type;
- source system;
- destination;
- schedule source;
- latest execution time;
- latest result;
- origin marker;
- suggested next step.

### Backup Artifact List

Artifacts include Restic snapshots, PBS backup entries, and cloud copy targets when reliably discoverable.

Each row shows:

- artifact type;
- repository or storage name;
- snapshot ID or archive identifier;
- creation time;
- source host;
- source path or VM/CT ID;
- size or changed data amount when available;
- current state;
- available actions.

The first release does not expose direct destructive backup-artifact deletion from this list. Retention cleanup remains a separate guarded operation.

### Restore Task List

Each restore row shows:

- restore task ID;
- source backup object;
- restored path scope;
- staging directory name;
- staging directory full path;
- final target path;
- creation time;
- current state;
- origin marker;
- continue or delete actions.

## Schedule And Notification Step

Schedule handling is capability-driven.

Preferred discovered schedule sources:

- OMV scheduled jobs on OMV hosts;
- systemd timers on Linux hosts;
- cron when systemd is unavailable;
- Windows local scheduling guidance for local Windows backup flows.

The schedule page explains and verifies:

- daily backup execution;
- weekly retention cleanup;
- monthly repository check;
- optional ZFS snapshot policy;
- email notification recipients and delivery settings.

The page must detect duplicate schedules and clearly distinguish:

- discovered existing schedule;
- app-managed schedule;
- conflicting duplicate schedule.

## Windows Local Backup

Windows support in the first release applies only to the current local Windows machine.

Source paths accept full drive roots or specific folders, one per line:

```text
D:\
E:\
D:\Finance
E:\Photos\Originals
```

The page explains:

- `C:\` is excluded unless explicitly entered;
- multi-value input is one path per line;
- quotes are not required for spaces or Chinese characters;
- UNC targets such as `\\10.0.0.10\DataBackup\Windows-PC` are expected;
- mirror mode is dangerous and can delete destination-only files.

The first release discovers local drives and app-managed Windows backup configuration. It does not attempt to take ownership of unrelated historical Windows backup jobs.

## Cloud Offsite Replication

The cloud page is centered on copying the encrypted Restic repository, not plaintext business folders.

It explains:

- provider selection;
- rclone authorization boundary;
- remote syntax;
- capacity checks;
- first sync;
- verification.

The application stores only remote selection and related metadata. OAuth tokens and provider credentials remain under rclone management.

## PVE And PBS

PVE/PBS remains an optional branch shown only when the host is identified as PVE and PBS-related capability checks succeed.

The page explains:

- guest discovery;
- PBS storage selection;
- backup mode;
- recent backup evidence;
- target PVE version compatibility notes;
- passthrough and storage risks;
- restore drill expectations.

The step never marks PVE protection complete from `vzdump` success alone. Completion requires backup evidence plus recorded restore-drill evidence.

## Page Instruction Pattern

Every workflow page uses the same structure:

1. what this step does;
2. why it matters;
3. current status;
4. required inputs;
5. discovered values and candidates;
6. recommended action;
7. danger notes;
8. success criteria;
9. exact next step.

Long explanations are broken into field-level help rather than placed in a large wall of text.

## Field-Level Help Standard

Every non-obvious field includes:

- purpose;
- realistic example;
- accepted format;
- multi-value rule when relevant;
- safety note when the value can overwrite, delete, or expose credentials;
- inline validation result;
- auto-detected candidates when available.

Examples:

- Windows source paths say `one path per line`;
- Restic include and exclude fields say `one entry per line`;
- dangerous path fields explicitly warn against `/tmp` and system locations;
- overwrite flows preview source and target paths before the user can continue.

## Danger Dialogs And Recovery Guidance

Any operation with destructive or high-impact consequences must open a guard dialog instead of executing immediately.

Such dialogs include:

- operation name;
- impact summary;
- exact path or object preview;
- why the operation is risky;
- recovery guidance;
- required confirmation text;
- safer alternative, when one exists.

Required examples:

- delete staging directory;
- overwrite original location from staging;
- enable Windows mirror mode;
- run Restic prune;
- move an old directory aside during Dataset migration;
- replace or remove duplicate schedule entries.

## Architecture Boundaries

The current lightweight server structure remains viable, but the next phase should split responsibilities more clearly.

Recommended modules:

- `profile.py`: platform and capability detection.
- `providers/`: host and capability adapters such as `zfs`, `restic`, `schedule`, `pve`, `omv`, and `windows_local`.
- `inventory.py`: normalized aggregation of discovered pools, tasks, artifacts, restore records, and warnings.
- `restore_center.py`: restore-task lifecycle, staging-root discovery, staging directory classification, and cleanup rules.
- `operations.py`: higher-level user actions that may map to multiple validated command previews.
- `evidence.py`: completion evidence used by workflow-state derivation.

The frontend should consume stable API payloads describing:

- current profile;
- available capabilities;
- discovered inventory;
- workflow state;
- latest relevant jobs;
- next-step recommendation.

## Safety And Error Handling

- Auto-discovery may suggest values but never silently saves destructive configuration.
- Unsupported capabilities hide the action instead of pretending success.
- Unverified discovered objects are labeled as such.
- Restore staging paths must never default to `/tmp` or other small system locations.
- Deletion and overwrite actions must be scoped to validated paths.
- Host-key verification remains enabled; the application must not silently trust unknown hosts.
- Secrets never appear in previews, logs, or job history.

## Testing Strategy

Unit tests cover:

- platform classification;
- capability classification;
- dataset and restore-root candidate filtering;
- restore staging directory classification;
- workflow-state derivation from evidence and inventory;
- path-safety validation;
- multi-line Windows and Restic input parsing.

HTTP tests cover:

- profile and inventory responses;
- workflow-state responses;
- skip and reopen behavior;
- restore-center list and delete endpoints;
- danger confirmation enforcement;
- secret redaction.

Frontend tests cover:

- host-aware step visibility;
- field-level help rendering;
- recommended-next-step behavior;
- staging directory list rendering;
- delete dialog behavior;
- warning and error presentation on mobile and desktop widths.

Real SSH, Docker, ZFS, Restic, rclone, OMV, PVE, PBS, Windows copy, backup, restore, migration, and network operations remain manual verification responsibilities under `CODEX_GUARD.md`.
