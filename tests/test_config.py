import tempfile
import unittest
from pathlib import Path

from backup_manager.config import AppConfig, BackupSet, ConfigStore, StorageTarget


class ConfigTests(unittest.TestCase):
    def test_default_config_is_not_tied_to_gensol(self):
        config = AppConfig.default()

        self.assertEqual(config.storage_targets, [])
        self.assertEqual(config.backup_sets, [])
        self.assertNotIn("Gensol", config.to_json())

    def test_round_trip_keeps_unicode_backup_paths(self):
        config = AppConfig(
            storage_targets=[
                StorageTarget(
                    id="nas",
                    name="NAS",
                    kind="zfs",
                    mountpoint="/Gensol",
                    pool_name="Gensol",
                )
            ],
            backup_sets=[
                BackupSet(
                    id="important",
                    name="重要资料",
                    include_paths=["/Gensol/财务"],
                    exclude_patterns=["Media"],
                )
            ],
        )

        restored = AppConfig.from_json(config.to_json())

        self.assertEqual(restored.backup_sets[0].include_paths[0], "/Gensol/财务")
        self.assertEqual(restored.storage_targets[0].pool_name, "Gensol")

    def test_ssh_defaults_use_existing_config_without_a_saved_password(self):
        config = AppConfig.default()

        self.assertEqual(config.ssh_auth_mode, "ssh_config")
        self.assertEqual(config.ssh_port, 22)
        self.assertNotIn("ssh_password", config.to_dict())

    def test_ssh_non_secret_settings_round_trip(self):
        config = AppConfig(
            executor_mode="ssh",
            ssh_host="10.0.0.10",
            ssh_user="root",
            ssh_port=2222,
            ssh_auth_mode="private_key",
            ssh_key_path="/root/.ssh/id_ed25519",
        )

        restored = AppConfig.from_json(config.to_json())

        self.assertEqual(restored.ssh_port, 2222)
        self.assertEqual(restored.ssh_auth_mode, "private_key")
        self.assertEqual(restored.ssh_key_path, "/root/.ssh/id_ed25519")

    def test_cloud_verification_is_cleared_when_remote_definition_changes(self):
        with tempfile.TemporaryDirectory() as temp:
            store = ConfigStore(Path(temp) / "config.json")
            store.save(
                AppConfig.from_dict(
                    {
                        "cloud_remote": {
                            "enabled": True,
                            "provider": "webdav",
                            "remote_name": "baidu-alist",
                            "remote_path": "backup/restic",
                            "verify_path": "backup",
                            "verified_at": "2026-06-24T09:00:00",
                        }
                    }
                )
            )

            updated = store.update(
                {
                    "cloud_remote": {
                        "remote_path": "backup/restic-v2",
                    }
                }
            )

        self.assertEqual(updated.cloud_remote.remote_path, "backup/restic-v2")
        self.assertEqual(updated.cloud_remote.verified_at, "")


if __name__ == "__main__":
    unittest.main()
