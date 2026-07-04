import unittest

from backup_manager.discovery import (
    parse_crontab_lines,
    parse_df,
    parse_remote_folders,
    parse_systemd_timers,
    parse_zfs_list,
    parse_zpool_list,
    suggest_restore_root_candidates,
    suggest_storage_targets,
)


class DiscoveryParsingTests(unittest.TestCase):
    def test_parse_zpool_list_returns_generic_pool_data(self):
        output = "Gensol\t27.3T\t5.37T\t12.7T\tONLINE\nTank\t8T\t1T\t7T\tONLINE\n"

        pools = parse_zpool_list(output)

        self.assertEqual(pools[0]["name"], "Gensol")
        self.assertEqual(pools[0]["free"], "12.7T")
        self.assertEqual(pools[1]["name"], "Tank")

    def test_parse_zfs_list_marks_dataset_mountpoints(self):
        output = (
            "Gensol\t/Gensol\t5.37T\t12.7T\n"
            "Gensol/finance\t/Gensol/finance\t20G\t12.7T\n"
        )

        datasets = parse_zfs_list(output)

        self.assertEqual(datasets[0]["name"], "Gensol")
        self.assertEqual(datasets[1]["mountpoint"], "/Gensol/finance")

    def test_parse_df_keeps_mountpoints_with_spaces(self):
        output = (
            "Filesystem      Size  Used Avail Use% Mounted on\n"
            "/dev/sda1        50G   20G   30G  40% /\n"
            "/dev/sdb1       100G   10G   90G  10% /mnt/USB Drive\n"
        )

        mounts = parse_df(output)

        self.assertEqual(mounts[1]["mountpoint"], "/mnt/USB Drive")
        self.assertEqual(mounts[1]["avail"], "90G")

    def test_parse_remote_folders_keeps_unicode_names(self):
        output = "财务\t/Gensol/财务\n共享网盘\t/Gensol/共享网盘\n"

        folders = parse_remote_folders(output)

        self.assertEqual(
            folders,
            [
                {"name": "财务", "path": "/Gensol/财务"},
                {"name": "共享网盘", "path": "/Gensol/共享网盘"},
            ],
        )

    def test_parse_systemd_timers_returns_schedule_rows(self):
        output = "daily.timer  Mon 2026-06-23 02:00:00 UTC  Mon 2026-06-22 02:00:00 UTC  /usr/local/sbin/restic-gensol-backup.sh\n"
        schedules = parse_systemd_timers(output)
        self.assertEqual(schedules[0]["type"], "systemd")

    def test_parse_crontab_lines_ignores_comments(self):
        output = "# comment\n0 2 * * * /usr/local/sbin/restic-gensol-backup.sh\n"
        schedules = parse_crontab_lines(output)
        self.assertEqual(schedules[0]["type"], "cron")

    def test_suggest_storage_targets_excludes_system_and_unmounted_datasets(self):
        datasets = [
            {"name": "rpool/ROOT", "mountpoint": "/", "used": "8G", "avail": "20G"},
            {"name": "rpool/var", "mountpoint": "/var", "used": "4G", "avail": "20G"},
            {"name": "tank", "mountpoint": "/tank", "used": "2T", "avail": "8T"},
            {"name": "tank/legacy", "mountpoint": "legacy", "used": "1G", "avail": "8T"},
            {"name": "tank/none", "mountpoint": "none", "used": "1G", "avail": "8T"},
        ]

        result = suggest_storage_targets(datasets)

        self.assertEqual(
            result,
            [
                {
                    "id": "discovered-tank",
                    "name": "tank",
                    "kind": "zfs",
                    "pool_name": "tank",
                    "mountpoint": "/tank",
                    "notes": "Automatically discovered. Confirm before saving.",
                }
            ],
        )

    def test_suggest_storage_targets_supports_child_datasets(self):
        datasets = [
            {
                "name": "tank/finance",
                "mountpoint": "/tank/finance",
                "used": "20G",
                "avail": "8T",
            }
        ]

        result = suggest_storage_targets(datasets)

        self.assertEqual(result[0]["id"], "discovered-tank-finance")
        self.assertEqual(result[0]["pool_name"], "tank")
        self.assertEqual(result[0]["mountpoint"], "/tank/finance")

    def test_suggest_storage_targets_deduplicates_mountpoints(self):
        datasets = [
            {"name": "tank", "mountpoint": "/tank", "used": "2T", "avail": "8T"},
            {"name": "tank/duplicate", "mountpoint": "/tank", "used": "2T", "avail": "8T"},
        ]

        result = suggest_storage_targets(datasets)

        self.assertEqual(len(result), 1)

    def test_suggest_restore_root_candidates_prefers_safe_dataset_mounts(self):
        datasets = [
            {"name": "rpool/ROOT", "mountpoint": "/", "used": "8G", "avail": "20G"},
            {"name": "tank", "mountpoint": "/tank", "used": "2T", "avail": "8T"},
        ]

        result = suggest_restore_root_candidates(datasets)

        self.assertEqual(
            result,
            [
                {
                    "id": "restore-root-tank",
                    "label": "tank restore root",
                    "path": "/tank/.backup-manager/restore",
                    "kind": "zfs_dataset",
                    "app_managed": True,
                }
            ],
        )


if __name__ == "__main__":
    unittest.main()
