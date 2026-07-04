import unittest

from backup_manager.config import AppConfig, RestoreRoot, StorageTarget
from backup_manager.workflow import derive_workflow


class WorkflowTests(unittest.TestCase):
    def test_new_config_starts_at_connection(self):
        result = derive_workflow(AppConfig.default(), [])

        self.assertEqual(result["next_step"], "connect")
        self.assertEqual(result["steps"][0]["status"], "not_started")

    def test_connection_requires_test_and_discovery_evidence(self):
        config = AppConfig.from_dict(
            {"workflow": {"completed_at": {"ssh_test": "2026-06-22T10:00:00"}}}
        )

        result = derive_workflow(config, [])

        connect = next(step for step in result["steps"] if step["id"] == "connect")
        self.assertEqual(connect["status"], "needs_attention")

        config.workflow.completed_at["storage_discovery"] = "2026-06-22T10:01:00"
        result = derive_workflow(config, [])
        connect = next(step for step in result["steps"] if step["id"] == "connect")
        self.assertEqual(connect["status"], "complete")

    def test_active_storage_completes_storage_step(self):
        config = AppConfig(
            storage_targets=[
                StorageTarget(
                    id="nas",
                    name="NAS",
                    kind="zfs",
                    mountpoint="/data",
                    pool_name="tank",
                )
            ],
            active_storage_id="nas",
        )

        result = derive_workflow(config, [])

        storage = next(step for step in result["steps"] if step["id"] == "storage")
        self.assertEqual(storage["status"], "complete")

    def test_restore_root_step_is_required_before_restore_center(self):
        config = AppConfig.from_dict(
            {
                "storage_targets": [
                    {
                        "id": "tank",
                        "name": "tank",
                        "kind": "zfs",
                        "mountpoint": "/tank",
                        "pool_name": "tank",
                    }
                ],
                "active_storage_id": "tank",
            }
        )
        result = derive_workflow(config, [])
        restore_root = next(
            step for step in result["steps"] if step["id"] == "restore_root"
        )
        restore_center = next(
            step for step in result["steps"] if step["id"] == "restore_center"
        )
        self.assertEqual(restore_root["status"], "not_started")
        self.assertEqual(restore_center["status"], "not_started")

    def test_restore_root_completes_when_active_root_is_saved(self):
        config = AppConfig(
            restore_roots=[
                RestoreRoot(
                    id="root-1",
                    label="Restore Root",
                    path="/tank/.backup-manager/restore",
                    kind="zfs_dataset",
                    app_managed=True,
                )
            ],
            active_restore_root_id="root-1",
        )
        result = derive_workflow(config, [])
        restore_root = next(
            step for step in result["steps"] if step["id"] == "restore_root"
        )
        self.assertEqual(restore_root["status"], "complete")

    def test_optional_step_can_be_skipped_and_reopened(self):
        config = AppConfig.from_dict(
            {"workflow": {"skipped_steps": {"dataset": "Not needed"}}}
        )

        result = derive_workflow(config, [])

        dataset = next(step for step in result["steps"] if step["id"] == "dataset")
        self.assertEqual(dataset["status"], "skipped")
        self.assertEqual(dataset["skip_reason"], "Not needed")

        del config.workflow.skipped_steps["dataset"]
        reopened = derive_workflow(config, [])
        dataset = next(step for step in reopened["steps"] if step["id"] == "dataset")
        self.assertEqual(dataset["status"], "not_started")

    def test_successful_jobs_complete_backup_and_restore_steps(self):
        jobs = [
            {
                "operation_id": "restic-backup",
                "status": "success",
                "finished_at": "2026-06-22T11:00:00",
            },
            {
                "operation_id": "restic-restore",
                "status": "success",
                "finished_at": "2026-06-22T12:00:00",
            },
        ]

        result = derive_workflow(AppConfig.default(), jobs)

        statuses = {step["id"]: step["status"] for step in result["steps"]}
        self.assertEqual(statuses["first_backup"], "complete")
        self.assertEqual(statuses["restore_center"], "complete")

    def test_windows_step_can_be_unavailable_on_non_windows_runtime(self):
        result = derive_workflow(
            AppConfig.default(), [], runtime={"local_platform": "linux"}
        )
        windows = next(step for step in result["steps"] if step["id"] == "windows")
        self.assertEqual(windows["status"], "unavailable")

    def test_verified_cloud_remote_completes_cloud_step(self):
        config = AppConfig.from_dict(
            {
                "cloud_remote": {
                    "enabled": True,
                    "provider": "webdav",
                    "remote_name": "baidu-alist",
                    "remote_path": "backup/restic",
                    "verified_at": "2026-06-24T10:00:00",
                }
            }
        )

        result = derive_workflow(config, [])

        cloud = next(step for step in result["steps"] if step["id"] == "cloud")
        self.assertEqual(cloud["status"], "complete")
        self.assertEqual(cloud["completed_at"], "2026-06-24T10:00:00")

    def test_workflow_never_serializes_connection_secrets(self):
        config = AppConfig.from_dict(
            {"workflow": {"completed_at": {"ssh_test": "2026-06-22T10:00:00"}}}
        )

        result = derive_workflow(config, [])

        self.assertNotIn("password", str(result).lower())
        self.assertNotIn("token", str(result).lower())


if __name__ == "__main__":
    unittest.main()
