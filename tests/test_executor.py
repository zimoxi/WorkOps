import unittest

from backup_manager.executor import (
    ExecutionResult,
    SshConnection,
    SshExecutor,
    build_ssh_invocation,
    classify_ssh_error,
)


class SshInvocationTests(unittest.TestCase):
    def test_private_key_uses_selected_port_and_key(self):
        connection = SshConnection(
            host="10.0.0.10",
            user="root",
            port=2222,
            auth_mode="private_key",
            key_path="/keys/omv",
        )

        argv, env, display = build_ssh_invocation(connection, ["zpool", "list"])

        self.assertIn("2222", argv)
        self.assertIn("/keys/omv", argv)
        self.assertEqual(env, {})
        self.assertNotIn("sshpass", argv)
        self.assertEqual(argv, display)

    def test_password_mode_uses_password_runner_without_exposing_secret(self):
        captured = {}

        def password_runner(connection, command):
            captured["connection"] = connection
            captured["command"] = command
            return ExecutionResult(
                0,
                "ok",
                "",
                ["paramiko", "root@nas", command],
                "ssh",
            )

        connection = SshConnection(
            host="nas",
            user="root",
            auth_mode="password",
            password="secret-value",
        )
        executor = SshExecutor(connection, password_runner=password_runner)

        result = executor.run_argv(["zfs", "list"])

        self.assertEqual(result.stdout, "ok")
        self.assertEqual(captured["command"], "'zfs' 'list'")
        self.assertIs(captured["connection"], connection)
        self.assertNotIn("secret-value", " ".join(result.command))

    def test_existing_config_does_not_force_a_key(self):
        connection = SshConnection(host="omv", user="root", auth_mode="ssh_config")

        argv, env, display = build_ssh_invocation(connection, ["true"])

        self.assertNotIn("-i", argv)
        self.assertIn("root@omv", argv)
        self.assertEqual(env, {})
        self.assertEqual(argv, display)

    def test_missing_password_is_rejected(self):
        connection = SshConnection(host="nas", auth_mode="password")
        executor = SshExecutor(
            connection,
            password_runner=lambda connection, command: self.fail(
                "runner must not be called"
            ),
        )

        result = executor.run_argv(["true"])

        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.error["code"], "invalid_connection")
        self.assertIn("密码", result.error["message"])

    def test_missing_private_key_path_is_rejected(self):
        connection = SshConnection(host="nas", auth_mode="private_key")

        with self.assertRaisesRegex(ValueError, "私钥"):
            build_ssh_invocation(connection, ["true"])

    def test_errors_are_actionable(self):
        error = classify_ssh_error("Permission denied (publickey,password).")

        self.assertEqual(error["code"], "authentication_failed")
        self.assertIn("凭据", error["message"])

    def test_host_key_errors_are_not_treated_as_password_errors(self):
        error = classify_ssh_error("Host key verification failed.")

        self.assertEqual(error["code"], "host_key_failed")
        self.assertIn("指纹", error["recovery"])

    def test_remote_missing_command_has_install_guidance(self):
        error = classify_ssh_error("sh: 1: zpool: command not found")

        self.assertEqual(error["code"], "remote_command_missing")
        self.assertIn("安装", error["recovery"])

    def test_missing_identity_file_takes_priority_over_permission_denied(self):
        error = classify_ssh_error(
            "Warning: Identity file /keys/omv not accessible: No such file.\n"
            "Permission denied (publickey)."
        )

        self.assertEqual(error["code"], "key_not_found")


if __name__ == "__main__":
    unittest.main()
