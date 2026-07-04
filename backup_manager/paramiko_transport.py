from __future__ import annotations

from pathlib import Path
import socket


def run_paramiko_command(
    connection,
    remote_command: str,
    *,
    paramiko_module=None,
    home: Path | None = None,
):
    from .executor import ExecutionResult, classify_ssh_error

    display_command = [
        "paramiko",
        f"{connection.user}@{connection.host}",
        remote_command,
    ]

    if paramiko_module is None:
        try:
            import paramiko as paramiko_module
        except ImportError:
            message = "Paramiko is not installed."
            return ExecutionResult(
                127,
                "",
                message,
                display_command,
                "ssh",
                {
                    "code": "client_missing",
                    "message": "密码模式缺少 Paramiko 组件。",
                    "recovery": "运行 py -m pip install -r requirements.txt 后重启应用。",
                },
            )

    client = paramiko_module.SSHClient()
    try:
        client.load_system_host_keys()
        known_hosts = (home or Path.home()) / ".ssh" / "known_hosts"
        if known_hosts.exists():
            client.load_host_keys(str(known_hosts))
        client.set_missing_host_key_policy(paramiko_module.RejectPolicy())
        client.connect(
            hostname=connection.host,
            port=connection.port,
            username=connection.user,
            password=connection.password,
            look_for_keys=False,
            allow_agent=False,
            timeout=10,
            auth_timeout=10,
            banner_timeout=10,
        )
        stdin, stdout, stderr = client.exec_command(remote_command, timeout=60)
        stdin.close()
        stdout_text = decode_stream(stdout.read())
        stderr_text = decode_stream(stderr.read())
        returncode = stdout.channel.recv_exit_status()
        error = classify_ssh_error(stderr_text) if returncode else None
        return ExecutionResult(
            returncode,
            stdout_text,
            stderr_text,
            display_command,
            "ssh",
            error,
        )
    except paramiko_module.AuthenticationException:
        return transport_error(
            display_command,
            "authentication_failed",
            "SSH 认证失败，请检查用户名和密码。",
            "确认该账户允许密码 SSH 登录。",
        )
    except paramiko_module.BadHostKeyException:
        return transport_error(
            display_command,
            "host_key_failed",
            "SSH 主机密钥与 known_hosts 中的记录不一致。",
            "立即停止连接，核对服务器指纹和 IP 是否发生变化。",
        )
    except paramiko_module.ssh_exception.NoValidConnectionsError as exc:
        return transport_error(
            display_command,
            "connection_refused",
            "SSH 连接失败。",
            "检查主机地址、端口、SSH 服务和防火墙。",
            str(exc),
        )
    except paramiko_module.SSHException as exc:
        detail = str(exc)
        if "not found in known_hosts" in detail.lower():
            command = f"ssh {connection.user}@{connection.host} -p {connection.port}"
            return transport_error(
                display_command,
                "host_key_unknown",
                "SSH 主机尚未加入 known_hosts。",
                f"先在终端运行 {command}，核对指纹后输入 yes。",
                detail,
            )
        error = classify_ssh_error(detail)
        return transport_error(
            display_command,
            error["code"],
            error["message"],
            error["recovery"],
            detail,
        )
    except socket.timeout as exc:
        return transport_error(
            display_command,
            "connection_timeout",
            "SSH 连接超时。",
            "检查主机地址、端口、防火墙和网络连通性。",
            str(exc),
        )
    except socket.gaierror as exc:
        return transport_error(
            display_command,
            "host_unreachable",
            "无法解析 SSH 主机。",
            "检查主机名、IP 地址和 DNS。",
            str(exc),
        )
    except OSError as exc:
        error = classify_ssh_error(str(exc))
        return transport_error(
            display_command,
            error["code"],
            error["message"],
            error["recovery"],
            str(exc),
        )
    finally:
        client.close()


def decode_stream(value) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def transport_error(
    display_command: list[str],
    code: str,
    message: str,
    recovery: str,
    detail: str = "",
):
    from .executor import ExecutionResult

    return ExecutionResult(
        255,
        "",
        detail,
        display_command,
        "ssh",
        {"code": code, "message": message, "recovery": recovery},
    )
