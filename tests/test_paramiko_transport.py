from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from backup_manager.executor import SshConnection
from backup_manager.paramiko_transport import run_paramiko_command


class AuthenticationException(Exception):
    pass


class BadHostKeyException(Exception):
    pass


class NoValidConnectionsError(Exception):
    pass


class SSHException(Exception):
    pass


class RejectPolicy:
    pass


class FakeChannel:
    def __init__(self, status):
        self.status = status

    def recv_exit_status(self):
        return self.status


class FakeStream:
    def __init__(self, value=b"", status=0):
        self.value = value
        self.channel = FakeChannel(status)

    def read(self):
        return self.value


class FakeStdin:
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


class FakeClient:
    def __init__(self, connect_error=None):
        self.connect_error = connect_error
        self.calls = []
        self.closed = False
        self.stdin = FakeStdin()

    def load_system_host_keys(self):
        self.calls.append(("load_system_host_keys",))

    def load_host_keys(self, path):
        self.calls.append(("load_host_keys", path))

    def set_missing_host_key_policy(self, policy):
        self.calls.append(("set_policy", type(policy)))

    def connect(self, **kwargs):
        self.calls.append(("connect", kwargs))
        if self.connect_error:
            raise self.connect_error

    def exec_command(self, command, timeout):
        self.calls.append(("exec_command", command, timeout))
        return self.stdin, FakeStream(b"ok\n", 0), FakeStream(b"", 0)

    def close(self):
        self.closed = True


def fake_paramiko(client):
    return SimpleNamespace(
        SSHClient=lambda: client,
        RejectPolicy=RejectPolicy,
        AuthenticationException=AuthenticationException,
        BadHostKeyException=BadHostKeyException,
        SSHException=SSHException,
        ssh_exception=SimpleNamespace(
            NoValidConnectionsError=NoValidConnectionsError
        ),
    )


class ParamikoTransportTests(unittest.TestCase):
    def test_password_connection_rejects_unknown_keys_and_disables_key_fallback(self):
        client = FakeClient()
        connection = SshConnection(
            host="10.0.0.10",
            user="root",
            port=22,
            auth_mode="password",
            password="secret-value",
        )
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp)
            known_hosts = home / ".ssh" / "known_hosts"
            known_hosts.parent.mkdir(parents=True)
            known_hosts.write_text("verified-host-key", encoding="utf-8")

            result = run_paramiko_command(
                connection,
                "'printf' 'backup-manager-ok'",
                paramiko_module=fake_paramiko(client),
                home=home,
            )

        connect_call = next(call for call in client.calls if call[0] == "connect")
        self.assertEqual(connect_call[1]["hostname"], "10.0.0.10")
        self.assertEqual(connect_call[1]["password"], "secret-value")
        self.assertFalse(connect_call[1]["look_for_keys"])
        self.assertFalse(connect_call[1]["allow_agent"])
        self.assertIn(("load_host_keys", str(known_hosts)), client.calls)
        self.assertIn(("set_policy", RejectPolicy), client.calls)
        self.assertEqual(result.stdout, "ok\n")
        self.assertNotIn("secret-value", " ".join(result.command))
        self.assertTrue(client.stdin.closed)
        self.assertTrue(client.closed)

    def test_authentication_error_is_structured_and_redacted(self):
        client = FakeClient(AuthenticationException("bad password"))
        connection = SshConnection(
            host="nas",
            user="root",
            auth_mode="password",
            password="secret-value",
        )

        result = run_paramiko_command(
            connection,
            "'true'",
            paramiko_module=fake_paramiko(client),
        )

        self.assertEqual(result.error["code"], "authentication_failed")
        self.assertNotIn("secret-value", " ".join(result.command))
        self.assertTrue(client.closed)

    def test_unknown_host_key_explains_how_to_verify_once(self):
        client = FakeClient(
            SSHException("Server '10.0.0.10' not found in known_hosts")
        )
        connection = SshConnection(
            host="10.0.0.10",
            user="root",
            port=22,
            auth_mode="password",
            password="secret-value",
        )

        result = run_paramiko_command(
            connection,
            "'true'",
            paramiko_module=fake_paramiko(client),
        )

        self.assertEqual(result.error["code"], "host_key_unknown")
        self.assertIn("ssh root@10.0.0.10 -p 22", result.error["recovery"])
        self.assertTrue(client.closed)


if __name__ == "__main__":
    unittest.main()
