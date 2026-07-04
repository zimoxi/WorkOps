import tempfile
import unittest
from pathlib import Path

from backup_manager.config import AppConfig, StorageTarget
from backup_manager.executor import ExecutionResult
from backup_manager.server import (
    AppContext,
    create_executor,
    discover_storage,
    json_response_payload,
    probe_ssh_connection,
)


class FakeExecutor:
    def __init__(self, outputs):
        self.outputs = outputs
        self.calls = []

    def run_argv(self, argv, command_env=(), cwd=""):
        self.calls.append(argv)
        stdout, stderr, returncode, error = self.outputs.get(
            argv[0], ("", "", 0, None)
        )
        return ExecutionResult(
            returncode, stdout, stderr, argv, "ssh", error
        )


class ServerTests(unittest.TestCase):
    def test_state_payload_contains_config_operations_and_jobs(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))

            payload = json_response_payload(context)

            self.assertIn("config", payload)
            self.assertIn("operations", payload)
            self.assertIn("jobs", payload)
            self.assertEqual(payload["config"]["storage_targets"], [])

    def test_remote_discovery_uses_executor_for_host_and_folder_commands(self):
        config = AppConfig(
            executor_mode="ssh",
            storage_targets=[
                StorageTarget(
                    id="nas",
                    name="NAS",
                    kind="zfs",
                    mountpoint="/Gensol",
                    pool_name="Gensol",
                )
            ],
            active_storage_id="nas",
        )
        executor = FakeExecutor(
            {
                "zpool": ("Gensol\t20T\t5T\t15T\tONLINE\n", "", 0, None),
                "zfs": ("Gensol\t/Gensol\t5T\t15T\n", "", 0, None),
                "df": ("Filesystem Size Used Avail Use% Mounted on\nGensol 20T 5T 15T 25% /Gensol\n", "", 0, None),
                "find": ("财务\t/Gensol/财务\n", "", 0, None),
            }
        )

        result = discover_storage(
            config,
            executor,
            profile_payload={"kind": "omv", "label": "OpenMediaVault", "source": "test"},
            capabilities={
                "zfs": True,
                "restic": False,
                "rclone": False,
                "systemd": False,
                "cron": False,
                "pbs": False,
                "smb": True,
            },
        )

        self.assertEqual(result["pools"][0]["name"], "Gensol")
        self.assertEqual(result["folders"][0]["name"], "财务")
        self.assertEqual([call[0] for call in executor.calls], ["zpool", "zfs", "df", "find"])
        self.assertEqual(result["errors"], [])

    def test_remote_discovery_returns_structured_command_errors(self):
        config = AppConfig(executor_mode="ssh")
        executor = FakeExecutor(
            {
                "zpool": (
                    "",
                    "zpool: command not found",
                    127,
                    {
                        "code": "remote_command_missing",
                        "message": "远程命令不可用。",
                        "recovery": "安装 ZFS 工具。",
                    },
                )
            }
        )

        result = discover_storage(config, executor)

        self.assertEqual(result["pools"], [])
        self.assertEqual(result["errors"][0]["code"], "remote_command_missing")

    def test_connection_probe_requires_expected_remote_marker(self):
        executor = FakeExecutor(
            {"printf": ("backup-manager-ok", "", 0, None)}
        )

        result = probe_ssh_connection(executor)

        self.assertTrue(result["ok"])
        self.assertEqual(executor.calls, [["printf", "backup-manager-ok"]])

    def test_ssh_mode_without_host_returns_a_validation_error(self):
        executor = create_executor(AppConfig(executor_mode="ssh"))

        result = probe_ssh_connection(executor)

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_connection")
        self.assertIn("Host", result["message"])


if __name__ == "__main__":
    unittest.main()
