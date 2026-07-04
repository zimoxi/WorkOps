from http.server import ThreadingHTTPServer
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from backup_manager.config import AppConfig
from backup_manager.executor import ExecutionResult
from backup_manager.server import AppContext, make_handler


class MarkerExecutor:
    def run_argv(self, argv, command_env=(), cwd=""):
        return ExecutionResult(0, "backup-manager-ok", "", argv, "ssh")


class SlowExecutor:
    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()
        self.returned = threading.Event()

    def run(self, command):
        self.started.set()
        self.release.wait(timeout=2)
        self.returned.set()
        return ExecutionResult(
            0,
            "Transferred: 128 MiB / 256 MiB, 50%, 4 MiB/s\nbackup-manager-ok",
            "",
            command.argv,
            "mock",
        )


class RunningServer:
    def __init__(self, context):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(context))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    @property
    def base_url(self):
        host, port = self.server.server_address
        return f"http://{host}:{port}"


def post_json(base_url, path, payload):
    request = Request(
        f"{base_url}{path}",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        response = urlopen(request, timeout=3)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    with response:
        return response.status, json.loads(response.read().decode("utf-8"))


def get_json(base_url, path):
    request = Request(f"{base_url}{path}", method="GET")
    try:
        response = urlopen(request, timeout=3)
    except HTTPError as exc:
        return exc.code, json.loads(exc.read().decode("utf-8"))
    with response:
        return response.status, json.loads(response.read().decode("utf-8"))


class HttpApiTests(unittest.TestCase):
    def test_state_includes_workflow(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/state")

            self.assertEqual(status, 200)
            self.assertIn("workflow", payload)
            self.assertEqual(payload["workflow"]["next_step"], "connect")

    def test_state_includes_profile_inventory_and_restore_center(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/state")

        self.assertEqual(status, 200)
        self.assertIn("profile", payload)
        self.assertIn("inventory", payload)
        self.assertIn("restore_center", payload["inventory"])

    def test_state_exposes_backup_tasks_and_warnings(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.config_store.save(
                AppConfig.from_dict(
                    {
                        "restic": {
                            "repository": "/tank/restic",
                            "password_file": "/root/.config/restic.pass",
                        },
                        "backup_sets": [
                            {
                                "id": "important",
                                "name": "Important",
                                "include_paths": ["/tank/SCAN"],
                            }
                        ],
                    }
                )
            )
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/state")

        self.assertEqual(status, 200)
        self.assertIn("backup_tasks", payload["inventory"])
        self.assertIn("warnings", payload["inventory"])

    def test_optional_step_can_be_skipped_and_reopened(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = post_json(
                    server.base_url,
                    "/api/workflow/step",
                    {
                        "step_id": "dataset",
                        "action": "skip",
                        "reason": "Not needed yet",
                    },
                )
                self.assertEqual(status, 200)
                self.assertEqual(payload["step"]["status"], "skipped")

                status, payload = post_json(
                    server.base_url,
                    "/api/workflow/step",
                    {"step_id": "dataset", "action": "reopen"},
                )

            self.assertEqual(status, 200)
            self.assertEqual(payload["step"]["status"], "not_started")

    def test_required_step_cannot_be_skipped(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = post_json(
                    server.base_url,
                    "/api/workflow/step",
                    {
                        "step_id": "restic",
                        "action": "skip",
                        "reason": "Skip required step",
                    },
                )

            self.assertEqual(status, 400)
            self.assertIn("cannot be skipped", payload["error"])

    def test_config_endpoint_never_persists_ssh_password(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = post_json(
                    server.base_url,
                    "/api/config",
                    {
                        "executor_mode": "ssh",
                        "ssh_host": "10.0.0.10",
                        "ssh_password": "must-not-be-saved",
                    },
                )

            self.assertEqual(status, 200)
            self.assertNotIn("ssh_password", payload["config"])
            self.assertNotIn(
                "must-not-be-saved",
                (Path(temp) / "config.json").read_text(encoding="utf-8"),
            )

    def test_config_endpoint_never_persists_cloud_secrets(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = post_json(
                    server.base_url,
                    "/api/config",
                    {
                        "cloud_remote": {
                            "enabled": True,
                            "provider": "webdav",
                            "remote_name": "baidu-alist",
                            "remote_path": "backup/restic",
                            "sync_source": "/ExamplePool/restic",
                            "notes": "session-only secret test",
                            "password": "must-not-be-saved",
                            "secret_access_key": "also-must-not-be-saved",
                            "access_key_id": "AKIA-SESSION-ONLY",
                            "bearer_token": "token-session-only",
                        }
                    },
                )

            self.assertEqual(status, 200)
            self.assertIn("cloud_remote", payload["config"])
            cloud_remote = payload["config"]["cloud_remote"]
            self.assertNotIn("password", cloud_remote)
            self.assertNotIn("secret_access_key", cloud_remote)
            self.assertNotIn("access_key_id", cloud_remote)
            self.assertNotIn("bearer_token", cloud_remote)
            saved = (Path(temp) / "config.json").read_text(encoding="utf-8")
            self.assertNotIn("must-not-be-saved", saved)
            self.assertNotIn("also-must-not-be-saved", saved)
            self.assertNotIn("AKIA-SESSION-ONLY", saved)
            self.assertNotIn("token-session-only", saved)

    def test_connection_endpoint_forwards_password_for_this_request_only(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.config_store.save(
                AppConfig(
                    executor_mode="ssh",
                    ssh_host="10.0.0.10",
                    ssh_auth_mode="password",
                )
            )
            with patch("backup_manager.server.create_executor") as factory:
                factory.return_value = MarkerExecutor()
                with RunningServer(context) as server:
                    status, payload = post_json(
                        server.base_url,
                        "/api/test-ssh",
                        {"ssh_password": "session-only"},
                    )

            self.assertEqual(status, 200)
            self.assertTrue(payload["ok"])
            self.assertEqual(factory.call_args.args[1], "session-only")
            self.assertNotIn(
                "session-only",
                (Path(temp) / "config.json").read_text(encoding="utf-8"),
            )

    def test_discovery_accepts_post_requests(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, payload = post_json(server.base_url, "/api/discover", {})

            self.assertEqual(status, 200)
            self.assertEqual(payload["pools"][0]["name"], "ExamplePool")
            self.assertEqual(payload["errors"], [])

    def test_restore_center_endpoint_lists_app_and_external_staging(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.config_store.save(
                AppConfig.from_dict(
                    {
                        "restore_roots": [
                            {
                                "id": "restore-root-ExamplePool",
                                "label": "ExamplePool restore root",
                                "path": "/ExamplePool/.backup-manager/restore",
                                "kind": "zfs_dataset",
                                "app_managed": True,
                            }
                        ],
                        "active_restore_root_id": "restore-root-ExamplePool",
                    }
                )
            )
            context.restore_store.save_task(
                {
                    "id": "restore-001",
                    "snapshot_id": "914ac36d",
                    "selected_paths": ["/Gensol/SCAN"],
                    "staging_name": "restore-001",
                    "staging_path": "/ExamplePool/.backup-manager/restore/restore-001",
                    "status": "cleanup_pending",
                    "origin": "app_managed",
                    "created_at": "2026-06-23T12:00:00",
                }
            )
            with RunningServer(context) as server:
                status, payload = get_json(server.base_url, "/api/restore-center")

        self.assertEqual(status, 200)
        self.assertIn("app_managed", payload)
        self.assertIn("external", payload)

    def test_restore_run_persists_restore_task_record(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.config_store.save(
                AppConfig.from_dict(
                    {
                        "restore_roots": [
                            {
                                "id": "restore-root-ExamplePool",
                                "label": "ExamplePool restore root",
                                "path": "/ExamplePool/.backup-manager/restore",
                                "kind": "zfs_dataset",
                                "app_managed": True,
                            }
                        ],
                        "active_restore_root_id": "restore-root-ExamplePool",
                        "restic": {
                            "repository": "/ExamplePool/restic",
                            "password_file": "/root/.config/restic.pass",
                        },
                    }
                )
            )
            with RunningServer(context) as server:
                status, payload = post_json(
                    server.base_url,
                    "/api/run",
                    {
                        "operation_id": "restic-restore",
                        "payload": {
                            "repository": "/ExamplePool/restic",
                            "password_file": "/root/.config/restic.pass",
                            "snapshot": "latest",
                            "target": "/ExamplePool/.backup-manager/restore/restore-test",
                            "paths": ["/ExamplePool/Finance"],
                        },
                        "confirmation": "I confirm the restore target is not a system path",
                    },
                )

        self.assertEqual(status, 200)
        app_managed = payload["inventory"]["restore_center"]["app_managed"]
        self.assertEqual(app_managed[0]["task_id"], "restore-restore-test")
        self.assertEqual(app_managed[0]["path"], "/ExamplePool/.backup-manager/restore/restore-test")
        self.assertEqual(app_managed[0]["status"], "restored_pending_review")

    def test_cloud_check_run_updates_verified_timestamp_and_returns_config(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            context.config_store.save(
                AppConfig.from_dict(
                    {
                        "cloud_remote": {
                            "enabled": True,
                            "provider": "webdav",
                            "remote_name": "baidu-alist",
                            "remote_path": "backup/restic",
                            "verify_path": "backup",
                            "sync_source": "/ExamplePool/restic",
                        }
                    }
                )
            )
            with RunningServer(context) as server:
                status, payload = post_json(
                    server.base_url,
                    "/api/run",
                    {
                        "operation_id": "cloud-rclone-check",
                        "payload": {
                            "remote": "baidu-alist:backup",
                        },
                    },
                )

        self.assertEqual(status, 200)
        self.assertIn("config", payload)
        self.assertEqual(payload["job"]["operation_id"], "cloud-rclone-check")
        self.assertTrue(payload["config"]["cloud_remote"]["verified_at"])
        cloud_step = next(
            step for step in payload["workflow"]["steps"] if step["id"] == "cloud"
        )
        self.assertEqual(cloud_step["status"], "complete")

    def test_cloud_list_and_pull_jobs_are_recorded_under_cloud_step(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            with RunningServer(context) as server:
                status, list_payload = post_json(
                    server.base_url,
                    "/api/run",
                    {
                        "operation_id": "cloud-rclone-list",
                        "payload": {
                            "remote": "baidu-alist:backup/restic",
                        },
                    },
                )
                self.assertEqual(status, 200)
                self.assertEqual(list_payload["job"]["step_id"], "cloud")

                status, pull_payload = post_json(
                    server.base_url,
                    "/api/run",
                    {
                        "operation_id": "cloud-rclone-pull",
                        "payload": {
                            "remote": "baidu-alist:backup/restic",
                            "target": "/ExamplePool/.backup-manager/restore/cloud-repo",
                        },
                        "confirmation": "I confirm the local cloud restore path has enough space",
                    },
                )

        self.assertEqual(status, 200)
        self.assertEqual(pull_payload["job"]["step_id"], "cloud")

    def test_async_run_returns_running_job_and_polling_returns_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            context = AppContext(Path(temp))
            slow_executor = SlowExecutor()
            with patch("backup_manager.server.create_executor", return_value=slow_executor):
                with RunningServer(context) as server:
                    status, payload = post_json(
                        server.base_url,
                        "/api/run",
                        {
                            "operation_id": "pve-list-guests",
                            "payload": {},
                            "async": True,
                        },
                    )

                    self.assertEqual(status, 202)
                    self.assertEqual(payload["job"]["status"], "running")
                    self.assertTrue(slow_executor.started.wait(timeout=1))

                    status, running_payload = get_json(
                        server.base_url, f"/api/jobs/{payload['job']['id']}"
                    )
                    self.assertEqual(status, 200)
                    self.assertEqual(running_payload["job"]["status"], "running")

                    slow_executor.release.set()
                    self.assertTrue(slow_executor.returned.wait(timeout=1))
                    time.sleep(0.05)

                    status, completed_payload = get_json(
                        server.base_url, f"/api/jobs/{payload['job']['id']}"
                    )

        self.assertEqual(status, 200)
        self.assertEqual(completed_payload["job"]["status"], "success")
        self.assertEqual(completed_payload["job"]["returncode"], 0)
        self.assertIn("inventory", completed_payload)


if __name__ == "__main__":
    unittest.main()
