import tempfile
import unittest
from pathlib import Path

from backup_manager.config import AppConfig
from backup_manager.restore_center import (
    RestoreStore,
    classify_staging_directories,
    validate_staging_delete_path,
)


class RestoreCenterTests(unittest.TestCase):
    def test_config_round_trips_restore_root_selection(self):
        config = AppConfig.from_dict(
            {
                "restore_roots": [
                    {
                        "id": "root-1",
                        "label": "Primary Restore Root",
                        "path": "/tank/.backup-manager/restore",
                        "kind": "zfs_dataset",
                        "app_managed": True,
                    }
                ],
                "active_restore_root_id": "root-1",
            }
        )

        restored = AppConfig.from_json(config.to_json())

        self.assertEqual(restored.active_restore_root_id, "root-1")
        self.assertEqual(
            restored.restore_roots[0].path, "/tank/.backup-manager/restore"
        )

    def test_restore_store_persists_restore_task_records(self):
        with tempfile.TemporaryDirectory() as temp:
            store = RestoreStore(Path(temp) / "restore_tasks.json")
            store.save_task(
                {
                    "id": "restore-001",
                    "snapshot_id": "914ac36d",
                    "selected_paths": ["/Gensol/SCAN"],
                    "staging_name": "restore-001",
                    "staging_path": "/Gensol/.backup-manager/restore/restore-001",
                    "status": "restored_pending_review",
                    "origin": "app_managed",
                    "created_at": "2026-06-23T12:00:00",
                }
            )

            tasks = store.list_tasks()

            self.assertEqual(tasks[0]["id"], "restore-001")
            self.assertEqual(tasks[0]["status"], "restored_pending_review")

    def test_classify_staging_directories_marks_external_entries(self):
        tasks = [
            {
                "id": "restore-001",
                "staging_name": "restore-001",
                "staging_path": "/tank/.backup-manager/restore/restore-001",
                "status": "cleanup_pending",
                "snapshot_id": "914ac36d",
                "created_at": "2026-06-23T12:00:00",
            }
        ]
        entries = [
            {
                "name": "restore-001",
                "path": "/tank/.backup-manager/restore/restore-001",
                "has_files": True,
            },
            {
                "name": "manual-copy",
                "path": "/tank/.backup-manager/restore/manual-copy",
                "has_files": True,
            },
        ]

        result = classify_staging_directories(tasks, entries)

        self.assertEqual(result["app_managed"][0]["status"], "cleanup_pending")
        self.assertEqual(result["external"][0]["name"], "manual-copy")

    def test_classify_staging_directories_keeps_missing_task_rows(self):
        tasks = [
            {
                "id": "restore-001",
                "staging_name": "restore-001",
                "staging_path": "/tank/.backup-manager/restore/restore-001",
                "status": "cleanup_complete",
                "snapshot_id": "914ac36d",
                "created_at": "2026-06-23T12:00:00",
            }
        ]

        result = classify_staging_directories(tasks, [])

        self.assertEqual(result["app_managed"][0]["task_id"], "restore-001")
        self.assertFalse(result["app_managed"][0]["has_files"])
        self.assertEqual(result["app_managed"][0]["status"], "cleanup_complete")

    def test_validate_staging_delete_path_blocks_escape(self):
        with self.assertRaises(ValueError):
            validate_staging_delete_path("/tank/.backup-manager/restore", "/tank")


if __name__ == "__main__":
    unittest.main()
