# SSH Authentication And Remote Discovery Design

## Goal

Allow each administrator to choose the SSH authentication method already used by their OMV or PVE system, then use that authenticated connection for discovery and all remote operations.

## Supported Authentication Modes

The storage page exposes three explicit modes:

1. `private_key`: use a private key file already available to the application process. In Docker, the operator mounts the key or `.ssh` directory read-only and enters the container path.
2. `password`: accept a password for the current connection. The password is held only in server memory for the request and is never written to `data/config.json`, job history, command previews, or logs.
3. `ssh_config`: rely on the user's existing OpenSSH configuration, SSH agent, or default key lookup. The host field may be an SSH config alias.

The existing host and user fields remain editable. Add a port field with default `22` and a key-path field shown only for `private_key`.

## Connection Flow

The UI saves non-secret connection settings, then provides a `Test SSH connection` action. Password mode asks for the password when testing, discovering, or running an operation; it does not persist it.

The server builds one `SshConnection` and uses it for:

- connection testing with `printf backup-manager-ok`;
- ZFS pool, dataset, and filesystem discovery;
- first-level folder discovery;
- white-listed backup, migration, cloud, and PVE/PBS commands.

Remote discovery must no longer call local `subprocess.run()` directly. It must use the selected executor and return structured errors when authentication, host-key validation, DNS/network access, or remote command availability fails.

## Host-Key Safety

Host-key checking stays enabled in both transports. OpenSSH never receives `StrictHostKeyChecking=no`, and Paramiko uses a reject policy rather than automatically adding keys. If a host is new or its key changed, the UI explains that the operator must verify the fingerprint and add or repair the host entry in the mounted or user-level `known_hosts` file.

## Password Transport

Password mode uses the Python Paramiko client on both Windows and Linux. It does not depend on `sshpass`, PuTTY, an interactive terminal, or a platform-specific password prompt. Private-key and `ssh_config` modes continue to use the system OpenSSH client so existing SSH config aliases and agents keep working.

Paramiko receives the password only in the request-scoped `SshConnection`. It connects with key lookup and SSH Agent authentication disabled for password mode, executes the same shell-quoted white-listed command used by the OpenSSH path, and closes the client after every operation. Passwords never appear in command arguments, API responses, saved config, or job history.

The client loads system host keys and the current user's `~/.ssh/known_hosts`, and uses a reject policy for unknown hosts. The application never auto-accepts an unknown or changed key. Authentication failures, unknown host keys, changed host keys, connection failures, and missing Paramiko installations are mapped to the existing structured error format.

Paramiko is declared in `requirements.txt` and installed by the Docker image. Windows setup installs the same requirements file before starting the application. `sshpass` is removed from the application runtime because password mode no longer invokes it.

## UI And Errors

Authentication-specific fields are conditionally visible. The page includes concise setup instructions for local Windows testing and OMV Docker deployment.

Connection results distinguish at least:

- connection successful;
- permission denied or wrong credentials;
- host key unknown or changed;
- connection timeout/refused;
- missing key file;
- missing `ssh` executable for private-key/config modes or missing Paramiko for password mode;
- remote `zpool` or `zfs` command unavailable.

Passwords and private-key contents never appear in API responses or job records.

## Testing

Unit tests cover OpenSSH argument construction, Paramiko password connection options, command quoting, password redaction, missing credentials, host-key rejection, remote discovery parsing, and error classification. HTTP tests cover the connection-test endpoint and verify password settings are not persisted. Existing command and server tests must continue to pass. A real Windows-to-OMV password connection test completes the runtime verification.

## Non-Goals

- The application will not generate or distribute SSH keys automatically.
- The application will not disable host-key checking.
- The application will not store reusable SSH passwords in this version.
- The application will not grant remote sudo permissions; the operator controls the remote account and its privileges.
