# Cross-Platform Paramiko Password Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make SSH password authentication work identically on Windows and in the OMV Docker container without `sshpass`.

**Architecture:** Password mode uses a focused Paramiko transport that loads verified host keys, disables key/agent fallback, executes one shell-quoted white-listed command, and returns the existing `ExecutionResult` shape. Private-key and SSH config/Agent modes stay on OpenSSH, preserving existing behavior.

**Tech Stack:** Python 3.11/3.12, Paramiko 5.0.0, OpenSSH, `unittest`, Docker Compose.

---

The directory is not a Git repository, so verification checkpoints replace commit steps.

### Task 1: Route Password Mode To A Dedicated Transport

**Files:**
- Modify: `tests/test_executor.py`
- Modify: `backup_manager/executor.py`

- [ ] **Step 1: Replace the sshpass expectation with a failing password-runner test**

```python
def test_password_mode_uses_password_runner_without_exposing_secret(self):
    captured = {}

    def password_runner(connection, command):
        captured["connection"] = connection
        captured["command"] = command
        return ExecutionResult(0, "ok", "", ["paramiko", "root@nas", command], "ssh")

    executor = SshExecutor(
        SshConnection(host="nas", user="root", auth_mode="password", password="secret"),
        password_runner=password_runner,
    )
    result = executor.run_argv(["zfs", "list"])

    self.assertEqual(result.stdout, "ok")
    self.assertEqual(captured["command"], "'zfs' 'list'")
    self.assertNotIn("secret", " ".join(result.command))
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run `py -m unittest tests.test_executor.SshInvocationTests.test_password_mode_uses_password_runner_without_exposing_secret -v`.

Expected: `SshExecutor` does not accept `password_runner`.

- [ ] **Step 3: Add password transport injection**

Change the constructor to:

```python
def __init__(self, connection: SshConnection, password_runner=None):
    self.connection = connection
    self.password_runner = password_runner
```

In `run_argv()`, validate host, port, and password, build the remote command with the existing `shell_quote()`, and call the injected password runner before building any OpenSSH invocation. When no runner was injected, import `run_paramiko_command` inside this password-only branch; this avoids a module import cycle. Remove password handling and `SSHPASS` from `build_ssh_invocation()`.

- [ ] **Step 4: Run executor tests and confirm GREEN**

Run `py -m unittest tests.test_executor -v`.

Expected: password mode uses the injected runner; key/config tests still pass.

### Task 2: Implement Strict Paramiko Password Execution

**Files:**
- Create: `backup_manager/paramiko_transport.py`
- Create: `tests/test_paramiko_transport.py`

- [ ] **Step 1: Write failing tests with a fake Paramiko client**

Tests must assert that the transport:

```python
client.load_system_host_keys()
client.load_host_keys(str(Path.home() / ".ssh" / "known_hosts"))
client.set_missing_host_key_policy(paramiko.RejectPolicy())
client.connect(
    hostname="10.0.0.10",
    port=22,
    username="root",
    password="secret",
    look_for_keys=False,
    allow_agent=False,
    timeout=10,
    auth_timeout=10,
    banner_timeout=10,
)
```

The fake channel returns UTF-8 stdout/stderr and an exit status. Separate tests map `AuthenticationException`, `BadHostKeyException`, unknown-host `SSHException`, `socket.timeout`, and missing Paramiko to structured errors without including the password.

- [ ] **Step 2: Run transport tests and confirm RED**

Run `py -m unittest tests.test_paramiko_transport -v`.

Expected: module import fails because `paramiko_transport.py` does not exist.

- [ ] **Step 3: Implement `run_paramiko_command()`**

Use this public signature:

```python
def run_paramiko_command(connection, remote_command: str) -> ExecutionResult:
```

Lazy-import Paramiko so key/config modes still work when the optional dependency is missing. Load system keys plus `~/.ssh/known_hosts` when present, set `RejectPolicy`, connect with password-only options, execute with a 60-second timeout, decode with UTF-8 replacement, receive the exit status, and close the client in `finally`.

Return display command data as:

```python
["paramiko", f"{connection.user}@{connection.host}", remote_command]
```

Map unknown hosts to recovery instructions containing `ssh <user>@<host> -p <port>` so the operator can verify and save the fingerprint once.

- [ ] **Step 4: Run transport and executor tests**

Run `py -m unittest tests.test_paramiko_transport tests.test_executor -v`.

Expected: all tests pass and no password appears in any result.

### Task 3: Package The Dependency On Windows And Docker

**Files:**
- Create: `requirements.txt`
- Modify: `docker/Dockerfile`
- Modify: `README.md`

- [ ] **Step 1: Declare Paramiko**

Create:

```text
paramiko==5.0.0
```

- [ ] **Step 2: Install requirements in Docker**

Copy `requirements.txt` before application files and run:

```dockerfile
RUN pip install --no-cache-dir -r requirements.txt
```

Remove `sshpass` from the apt package list; retain `openssh-client` for key/config modes.

- [ ] **Step 3: Update Windows and Docker instructions**

Windows setup uses:

```powershell
py -m pip install -r requirements.txt
```

Explain that first password connection requires a verified `known_hosts` entry and show:

```powershell
ssh root@10.0.0.10 -p 22
```

Remove every statement that password mode requires `sshpass`.

- [ ] **Step 4: Install the dependency locally**

Run `py -m pip install -r requirements.txt`.

Expected: Paramiko 5.0.0 imports successfully.

### Task 4: Full Verification

**Files:**
- No source changes expected unless a test identifies a defect.

- [ ] **Step 1: Run all automated checks**

```powershell
py -m unittest discover -s tests -v
py -m compileall -f backup_manager run.py
node --check static/app.js
```

Expected: all tests pass, compilation succeeds, and JavaScript syntax exits 0.

- [ ] **Step 2: Restart the Windows server**

Stop only the process listening on `127.0.0.1:8099`, then start `py run.py --host 127.0.0.1 --port 8099` hidden.

- [ ] **Step 3: Verify runtime readiness**

Confirm Paramiko imports in the same Python interpreter running the server, `/api/state` contains no password field, and TCP port `10.0.0.10:22` is reachable.

- [ ] **Step 4: Complete user-owned credential verification**

The operator verifies the SSH fingerprint with OpenSSH, enters the password in the web page, and clicks `Test SSH connection`. No automated script reads or stores the user's password.
