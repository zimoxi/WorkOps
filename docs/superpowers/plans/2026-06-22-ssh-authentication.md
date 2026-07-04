# SSH Authentication And Remote Discovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let administrators select their existing SSH authentication method and use that authenticated connection for host testing, ZFS discovery, folder discovery, and white-listed remote operations.

**Architecture:** Extend `AppConfig` with non-secret SSH settings, model connection credentials separately per request, and give `SshExecutor` one raw-command execution path shared by discovery and prepared operations. Passwords travel only in POST request memory through `SSHPASS`; API responses, saved config, and job history receive only redacted command metadata.

**Tech Stack:** Python 3.12 standard library, OpenSSH client, `sshpass` for optional password mode, vanilla JavaScript, `unittest`, Docker Compose.

---

## File Map

- Modify `backup_manager/config.py`: persist authentication mode, SSH port, and key path only.
- Modify `backup_manager/executor.py`: build and execute SSH commands for private-key, password, and existing-config modes; classify connection failures.
- Modify `backup_manager/discovery.py`: parse remote first-level folder output.
- Modify `backup_manager/server.py`: route discovery and connection tests through the selected executor and keep passwords request-scoped.
- Modify `static/app.js`: add authentication selector, conditional fields, password prompt, connection test, and visible errors.
- Modify `static/styles.css`: style authentication help and connection-result states.
- Modify `docker/Dockerfile`: install `sshpass` alongside OpenSSH.
- Modify `docker-compose.yml`: document read-only SSH mounts and optional agent socket.
- Modify `README.md`: document all authentication modes and host-key setup.
- Create `tests/test_executor.py`: SSH construction, redaction, and error classification tests.
- Modify `tests/test_config.py`, `tests/test_discovery.py`, and `tests/test_server.py`: configuration, remote discovery, and API security tests.

The directory is not currently a Git repository, so this plan uses verification checkpoints instead of commit steps.

### Task 1: Persist Only Non-Secret SSH Settings

**Files:**
- Modify: `backup_manager/config.py`
- Modify: `tests/test_config.py`

- [ ] **Step 1: Write failing configuration tests**

Add tests that require defaults and round-trip behavior:

```python
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
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```powershell
python -m unittest tests.test_config -v
```

Expected: failures because `ssh_port` and `ssh_auth_mode` do not exist.

- [ ] **Step 3: Add the configuration fields**

Add to `AppConfig`:

```python
ssh_port: int = 22
ssh_auth_mode: str = "ssh_config"
```

Read them in `from_dict()` with:

```python
ssh_port=int(data.get("ssh_port", 22)),
ssh_auth_mode=data.get("ssh_auth_mode", "ssh_config"),
```

Do not add any password property to `AppConfig`.

- [ ] **Step 4: Run the configuration tests and confirm GREEN**

Run `python -m unittest tests.test_config -v`.

Expected: all configuration tests pass.

### Task 2: Implement Selectable SSH Authentication

**Files:**
- Create: `tests/test_executor.py`
- Modify: `backup_manager/executor.py`

- [ ] **Step 1: Write failing executor tests**

Create tests for the wished-for `SshConnection`, `build_ssh_invocation()`, and `classify_ssh_error()` APIs:

```python
import unittest

from backup_manager.executor import SshConnection, build_ssh_invocation, classify_ssh_error


class SshInvocationTests(unittest.TestCase):
    def test_private_key_uses_selected_port_and_key(self):
        connection = SshConnection(
            host="10.0.0.10", user="root", port=2222,
            auth_mode="private_key", key_path="/keys/omv",
        )
        argv, env, display = build_ssh_invocation(connection, ["zpool", "list"])
        self.assertIn("2222", argv)
        self.assertIn("/keys/omv", argv)
        self.assertEqual(env, {})
        self.assertNotIn("sshpass", argv)

    def test_password_uses_environment_and_redacts_display(self):
        connection = SshConnection(
            host="nas", user="root", auth_mode="password", password="secret-value",
        )
        argv, env, display = build_ssh_invocation(connection, ["zfs", "list"])
        self.assertEqual(argv[:2], ["sshpass", "-e"])
        self.assertEqual(env["SSHPASS"], "secret-value")
        self.assertNotIn("secret-value", " ".join(display))

    def test_existing_config_does_not_force_a_key(self):
        connection = SshConnection(host="omv", user="root", auth_mode="ssh_config")
        argv, env, display = build_ssh_invocation(connection, ["true"])
        self.assertNotIn("-i", argv)
        self.assertIn("root@omv", argv)

    def test_errors_are_actionable(self):
        error = classify_ssh_error("Permission denied (publickey,password).")
        self.assertEqual(error["code"], "authentication_failed")
        self.assertIn("凭据", error["message"])
```

- [ ] **Step 2: Run the executor tests and confirm RED**

Run `python -m unittest tests.test_executor -v`.

Expected: import failure because the new APIs do not exist.

- [ ] **Step 3: Implement connection modeling and command construction**

Add:

```python
@dataclass(frozen=True)
class SshConnection:
    host: str
    user: str = "root"
    port: int = 22
    auth_mode: str = "ssh_config"
    key_path: str = ""
    password: str = ""


def build_ssh_invocation(connection: SshConnection, remote_argv: list[str]):
    if not connection.host:
        raise ValueError("SSH Host 不能为空")
    remote_command = " ".join(shell_quote(part) for part in remote_argv)
    ssh = ["ssh", "-p", str(connection.port), "-o", "ConnectTimeout=10"]
    env: dict[str, str] = {}
    if connection.auth_mode == "private_key":
        if not connection.key_path:
            raise ValueError("私钥模式需要填写私钥路径")
        ssh.extend(["-o", "BatchMode=yes", "-i", connection.key_path])
    elif connection.auth_mode == "password":
        if not connection.password:
            raise ValueError("密码模式需要输入 SSH 密码")
        ssh.extend([
            "-o", "BatchMode=no",
            "-o", "PreferredAuthentications=password,keyboard-interactive",
            "-o", "PubkeyAuthentication=no",
        ])
        env["SSHPASS"] = connection.password
        ssh = ["sshpass", "-e", *ssh]
    elif connection.auth_mode == "ssh_config":
        ssh.extend(["-o", "BatchMode=yes"])
    else:
        raise ValueError("不支持的 SSH 认证方式")
    argv = [*ssh, f"{connection.user}@{connection.host}", remote_command]
    return argv, env, list(argv)
```

Implement `classify_ssh_error()` using stable OpenSSH phrases for permission denied, host-key errors, timeout/refused, and missing executables. Preserve host-key checking by not adding any option that disables it.

- [ ] **Step 4: Refactor `SshExecutor` around the shared builder**

Give the executor `run_argv(remote_argv, command_env=())`. Merge `SSHPASS` into a copied process environment, catch `FileNotFoundError` and `TimeoutExpired`, and return only the redacted display command. Make existing `run(PreparedCommand)` delegate to `run_argv()`.

- [ ] **Step 5: Run executor and existing command tests**

Run:

```powershell
python -m unittest tests.test_executor tests.test_commands -v
```

Expected: all tests pass and no secret appears in output.

### Task 3: Route Discovery Through The Selected Executor

**Files:**
- Modify: `backup_manager/discovery.py`
- Modify: `backup_manager/server.py`
- Modify: `tests/test_discovery.py`
- Modify: `tests/test_server.py`

- [ ] **Step 1: Write failing folder parsing and remote discovery tests**

Add:

```python
def test_parse_remote_folders_keeps_unicode_names(self):
    output = "财务\t/Gensol/财务\n共享网盘\t/Gensol/共享网盘\n"
    self.assertEqual(
        parse_remote_folders(output),
        [
            {"name": "财务", "path": "/Gensol/财务"},
            {"name": "共享网盘", "path": "/Gensol/共享网盘"},
        ],
    )
```

In `test_server.py`, use a fake executor whose `run_argv()` returns known outputs and assert that `discover_storage(config, fake)` returns the parsed remote pool and folders. Also assert that a config patch containing `ssh_password` does not serialize that key.

- [ ] **Step 2: Run discovery/server tests and confirm RED**

Run:

```powershell
python -m unittest tests.test_discovery tests.test_server -v
```

Expected: failures because parsing and executor injection do not exist.

- [ ] **Step 3: Implement remote folder parsing**

Add:

```python
def parse_remote_folders(output: str) -> list[dict[str, str]]:
    folders = []
    for line in output.splitlines():
        if not line.strip():
            continue
        name, separator, path = line.partition("\t")
        if separator and name and path:
            folders.append({"name": name, "path": path})
    return folders
```

- [ ] **Step 4: Refactor discovery into executor-backed reads**

Change the effective signature to:

```python
def discover_storage(config: AppConfig, executor=None) -> dict[str, Any]:
```

For SSH mode, execute these remote argv lists through `run_argv()`:

```python
["zpool", "list", "-H", "-o", "name,size,allocated,free,health"]
["zfs", "list", "-H", "-o", "name,mountpoint,used,avail"]
["df", "-h"]
["find", mountpoint, "-mindepth", "1", "-maxdepth", "1", "-type", "d", "-printf", "%f\\t%p\\n"]
```

Keep mock behavior unchanged. Local mode may continue using `LocalExecutor`, but it must use the same `run_argv()` interface.

- [ ] **Step 5: Add request-scoped connection endpoints**

Implement POST `/api/test-ssh` and POST `/api/discover`. Both accept optional `ssh_password` outside config data. Build the executor with:

```python
def create_executor(config: AppConfig, password: str = ""):
    connection = SshConnection(
        host=config.ssh_host,
        user=config.ssh_user,
        port=config.ssh_port,
        auth_mode=config.ssh_auth_mode,
        key_path=config.ssh_key_path,
        password=password,
    )
    return SshExecutor(connection)
```

Connection testing executes `["printf", "backup-manager-ok"]`. Reject `ssh_password` in `/api/config` before `ConfigStore.update()` so it cannot become persisted data. Pass the request password into `/api/run` without including it in the job record.

- [ ] **Step 6: Run discovery/server tests and confirm GREEN**

Run `python -m unittest tests.test_discovery tests.test_server -v`.

Expected: remote output is parsed, secrets are absent from persisted JSON, and connection errors are structured.

### Task 4: Add Authentication Controls And Connection Feedback

**Files:**
- Modify: `static/app.js`
- Modify: `static/styles.css`

- [ ] **Step 1: Add selectable authentication controls**

Extend the storage form with:

```html
<select id="sshAuthMode" onchange="renderSshAuthFields()">
  <option value="ssh_config">已有 SSH 配置 / Agent</option>
  <option value="private_key">SSH 私钥</option>
  <option value="password">SSH 密码</option>
</select>
<input id="sshPort" type="number" min="1" max="65535" value="22">
<div id="sshAuthFields"></div>
<div id="sshConnectionResult" role="status"></div>
```

`private_key` renders a key-path input, `password` renders a password input with `autocomplete="current-password"`, and `ssh_config` renders concise guidance only. Do not put the password into `state.config`.

- [ ] **Step 2: Save only non-secret fields**

Update `saveRuntimeConfig()` to send `ssh_port`, `ssh_auth_mode`, and `ssh_key_path`. Never include the password input in `/api/config`.

- [ ] **Step 3: Use POST requests for testing and discovery**

Add:

```javascript
function currentSshPassword() {
  return document.querySelector("#sshPassword")?.value || "";
}

async function testSshConnection() {
  await saveRuntimeConfig();
  const payload = await api("/api/test-ssh", {
    method: "POST",
    body: JSON.stringify({ ssh_password: currentSshPassword() }),
  });
  renderConnectionResult(payload);
}
```

Change `discover()` to POST the same request-scoped password. Wrap both functions in `try/catch`, keeping the page usable and displaying the structured recovery message.

- [ ] **Step 4: Style stable states**

Add `.connection-result`, `.connection-result.success`, and `.connection-result.error` styles with restrained green/red accents. Keep authentication fields in the existing responsive grid and ensure long key paths wrap or truncate without changing the layout width.

- [ ] **Step 5: Run JavaScript syntax validation**

Run:

```powershell
node --check static/app.js
```

Expected: exit code 0.

### Task 5: Package Password Support And Document Setup

**Files:**
- Modify: `docker/Dockerfile`
- Modify: `docker-compose.yml`
- Modify: `README.md`

- [ ] **Step 1: Add optional password-mode dependency**

Add `sshpass` to the existing `apt-get install` line in `docker/Dockerfile`.

- [ ] **Step 2: Document safe mounts**

Keep the existing no-privileged/no-docker-socket posture. Add examples to `docker-compose.yml` comments:

```yaml
# Private key and known_hosts mode:
# - /root/.ssh:/root/.ssh:ro
# Existing SSH agent mode, when an agent socket is available:
# - ${SSH_AUTH_SOCK}:/ssh-agent
# environment:
#   SSH_AUTH_SOCK: /ssh-agent
```

- [ ] **Step 3: Document all three connection methods**

README instructions must explain:

- private-key mode requires a read-only mounted key and `known_hosts`;
- password mode is request-scoped, not saved, and requires `sshpass` in the runtime;
- existing-config mode uses OpenSSH defaults, config aliases, or an agent;
- first connection requires fingerprint verification;
- Windows local testing can use mock mode, while Windows SSH-agent/config mode requires the system OpenSSH client;
- a changed host key must be investigated rather than bypassed.

- [ ] **Step 4: Run the complete automated suite**

Run:

```powershell
python -m unittest discover -s tests -v
python -m compileall backup_manager run.py
node --check static/app.js
```

Expected: all tests pass, Python compilation succeeds, and JavaScript syntax check exits 0.

### Task 6: Browser And Runtime Verification

**Files:**
- No source changes expected unless verification exposes a defect.

- [ ] **Step 1: Start the Windows development server**

Run:

```powershell
python run.py --host 127.0.0.1 --port 8099
```

Expected: `Backup Manager listening on http://127.0.0.1:8099`.

- [ ] **Step 2: Verify the authentication UI at desktop and mobile widths**

Check that selecting each mode displays only its relevant fields, long paths do not overflow, and connection errors remain readable at 1440x900 and 390x844.

- [ ] **Step 3: Verify HTTP behavior without a real OMV credential**

Confirm `/api/state` does not contain `ssh_password`; password-mode requests with an empty password return a clear validation error; mock discovery still works.

- [ ] **Step 4: Report the real-host verification boundary**

Docker image construction and a real OMV/PVE SSH login require the target machine. Provide the OMV deployment commands and ask the operator to test `Test SSH connection` before any backup operation.
