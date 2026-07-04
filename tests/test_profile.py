import unittest

from backup_manager.profile import (
    detect_local_platform,
    detect_remote_capabilities,
    detect_remote_platform,
)


class ProfileTests(unittest.TestCase):
    def test_local_windows_is_classified_as_windows_local(self):
        profile = detect_local_platform(system_name="Windows")
        self.assertEqual(profile["kind"], "windows-local")

    def test_remote_pve_wins_over_generic_linux(self):
        profile = detect_remote_platform(
            command_presence={
                "pveversion": True,
                "qm": True,
                "pct": True,
                "pvesm": True,
            }
        )
        self.assertEqual(profile["kind"], "pve")

    def test_remote_omv_is_detected_when_pve_commands_are_missing(self):
        profile = detect_remote_platform(
            command_presence={"omv-confdbadm": True, "pveversion": False}
        )
        self.assertEqual(profile["kind"], "omv")

    def test_capability_detection_is_independent_of_platform(self):
        capabilities = detect_remote_capabilities(
            command_presence={
                "zpool": True,
                "zfs": True,
                "restic": False,
                "rclone": True,
                "systemctl": True,
                "crontab": False,
            }
        )
        self.assertTrue(capabilities["zfs"])
        self.assertFalse(capabilities["restic"])
        self.assertTrue(capabilities["rclone"])
        self.assertTrue(capabilities["systemd"])


if __name__ == "__main__":
    unittest.main()
