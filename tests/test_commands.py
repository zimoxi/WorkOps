import unittest

from backup_manager.commands import (
    CommandCatalog,
    OperationError,
    build_restic_environment,
    validate_restore_target,
)


class CommandCatalogTests(unittest.TestCase):
    def test_rejects_unknown_command(self):
        catalog = CommandCatalog()

        with self.assertRaises(OperationError):
            catalog.build("rm-everything", {})

    def test_restore_target_rejects_tmp_and_root_paths(self):
        for path in ["/tmp", "/tmp/restore-test", "/", "/var", ""]:
            with self.subTest(path=path):
                with self.assertRaises(OperationError):
                    validate_restore_target(path)

    def test_restic_backup_command_uses_configured_paths(self):
        catalog = CommandCatalog()
        command = catalog.build(
            "restic-backup",
            {
                "repository": "/pool/_cloud_restic/repo",
                "password_file": "/root/restic.pass",
                "include_paths": ["/pool/finance", "/pool/docs"],
                "exclude_file": "/root/excludes.txt",
                "tag": "important",
            },
        )

        self.assertIn("RESTIC_REPOSITORY=/pool/_cloud_restic/repo", command.env)
        self.assertIn("/pool/finance", command.argv)
        self.assertIn("--exclude-file", command.argv)

    def test_restic_environment_requires_repository_and_password_file(self):
        with self.assertRaises(OperationError):
            build_restic_environment("", "/root/pass")
        with self.assertRaises(OperationError):
            build_restic_environment("/repo", "")

    def test_windows_preview_accepts_specific_absolute_folder(self):
        catalog = CommandCatalog()
        command = catalog.build(
            "windows-robocopy-preview",
            {
                "source": "D:\\Finance Records",
                "target": "\\\\10.0.0.10\\Backup\\Windows-PC",
            },
        )

        self.assertEqual(command.argv[1], "D:\\Finance Records")
        self.assertEqual(
            command.argv[2],
            "\\\\10.0.0.10\\Backup\\Windows-PC\\D-Finance Records",
        )

    def test_windows_preview_rejects_relative_source(self):
        catalog = CommandCatalog()
        with self.assertRaises(OperationError):
            catalog.build(
                "windows-robocopy-preview",
                {"source": "Finance", "target": "\\\\server\\backup"},
            )

    def test_cloud_check_command_uses_remote_target(self):
        catalog = CommandCatalog()

        command = catalog.build(
            "cloud-rclone-check",
            {"remote": "baidu-alist:backup"},
        )

        self.assertEqual(
            command.argv,
            ["rclone", "lsd", "baidu-alist:backup"],
        )
        self.assertEqual(command.id, "cloud-rclone-check")

    def test_cloud_list_command_uses_machine_readable_listing(self):
        catalog = CommandCatalog()

        command = catalog.build(
            "cloud-rclone-list",
            {"remote": "baidu-alist:backup/restic"},
        )

        self.assertEqual(
            command.argv,
            ["rclone", "lsf", "baidu-alist:backup/restic"],
        )

    def test_cloud_pull_command_copies_remote_repo_to_local_target(self):
        catalog = CommandCatalog()

        command = catalog.build(
            "cloud-rclone-pull",
            {
                "remote": "baidu-alist:backup/restic",
                "target": "/ExamplePool/.backup-manager/restore/cloud-repo-20260624",
            },
        )

        self.assertEqual(
            command.argv,
            [
                "rclone",
                "copy",
                "baidu-alist:backup/restic",
                "/ExamplePool/.backup-manager/restore/cloud-repo-20260624",
                "--progress",
            ],
        )
        self.assertEqual(
            command.confirm_text,
            "I confirm the local cloud restore path has enough space",
        )


if __name__ == "__main__":
    unittest.main()
