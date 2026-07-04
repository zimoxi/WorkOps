import unittest

from backup_manager.inventory import build_inventory


class InventoryTests(unittest.TestCase):
    def test_inventory_includes_app_managed_and_external_staging_lists(self):
        inventory = build_inventory(
            config={
                "active_storage_id": "tank",
                "restic": {"repository": "/tank/restic"},
            },
            profile={"kind": "omv"},
            capabilities={"zfs": True, "restic": True},
            discovery={
                "pools": [{"name": "tank", "free": "8T"}],
                "datasets": [
                    {
                        "name": "tank",
                        "mountpoint": "/tank",
                        "used": "2T",
                        "avail": "8T",
                    }
                ],
            },
            restore_tasks=[
                {
                    "id": "restore-001",
                    "staging_path": "/tank/.backup-manager/restore/restore-001",
                    "staging_name": "restore-001",
                    "snapshot_id": "914ac36d",
                    "status": "cleanup_pending",
                    "created_at": "2026-06-23T12:00:00",
                }
            ],
            staging_entries=[
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
            ],
            jobs=[],
        )

        self.assertEqual(
            inventory["restore_center"]["app_managed"][0]["task_id"], "restore-001"
        )
        self.assertEqual(
            inventory["restore_center"]["external"][0]["name"], "manual-copy"
        )

    def test_inventory_builds_backup_task_rows_from_config_and_jobs(self):
        inventory = build_inventory(
            config={
                "restic": {
                    "repository": "/tank/restic",
                    "password_file": "/root/.config/restic.pass",
                },
                "backup_sets": [
                    {"id": "important", "name": "Important", "include_paths": ["/tank/SCAN"]}
                ],
                "windows_backup": {
                    "enabled": True,
                    "source_drives": ["D:\\", "E:\\"],
                    "smb_target": "\\\\10.0.0.10\\Backup",
                },
                "cloud_remote": {
                    "enabled": True,
                    "remote_name": "baidu-alist",
                    "remote_path": "backup/restic",
                    "sync_source": "/tank/restic",
                    "verify_path": "backup",
                    "verified_at": "2026-06-24T10:00:00",
                },
                "pve_pbs": {
                    "enabled": True,
                    "pve_host": "10.0.0.3",
                    "pbs_storage": "pbs-store",
                },
            },
            profile={"kind": "pve"},
            capabilities={"restic": True, "rclone": True, "pbs": True},
            discovery={"pools": [], "datasets": [], "schedules": []},
            restore_tasks=[],
            staging_entries=[],
            jobs=[
                {
                    "operation_id": "restic-backup",
                    "status": "success",
                    "finished_at": "2026-06-23T08:00:00",
                },
                {
                    "operation_id": "cloud-rclone-sync",
                    "status": "failed",
                    "finished_at": "2026-06-23T09:00:00",
                },
            ],
        )

        self.assertEqual(inventory["backup_tasks"][0]["type"], "restic")
        self.assertEqual(inventory["backup_tasks"][0]["latest_result"], "success")
        self.assertEqual(inventory["backup_tasks"][1]["type"], "windows_local")
        self.assertEqual(
            inventory["backup_tasks"][2]["destination"],
            "baidu-alist:backup/restic",
        )
        self.assertEqual(
            inventory["backup_tasks"][2]["verified_at"],
            "2026-06-24T10:00:00",
        )

    def test_inventory_warns_when_duplicate_schedules_are_discovered(self):
        inventory = build_inventory(
            config={"restic": {"repository": "/tank/restic"}},
            profile={"kind": "omv"},
            capabilities={"systemd": True},
            discovery={
                "pools": [],
                "datasets": [],
                "schedules": [
                    {
                        "id": "daily-backup-a",
                        "type": "systemd",
                        "command": "/usr/local/sbin/restic-gensol-backup.sh",
                    },
                    {
                        "id": "daily-backup-b",
                        "type": "cron",
                        "command": "/usr/local/sbin/restic-gensol-backup.sh",
                    },
                ],
            },
            restore_tasks=[],
            staging_entries=[],
            jobs=[],
        )

        self.assertIn(
            "duplicate_schedule", [item["code"] for item in inventory["warnings"]]
        )


if __name__ == "__main__":
    unittest.main()
