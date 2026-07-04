from __future__ import annotations

from dataclasses import asdict, dataclass
import os
import subprocess
from typing import Protocol

from .commands import PreparedCommand


@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    command: list[str]
    mode: str
    error: dict[str, str] | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class Executor(Protocol):
    def run(self, command: PreparedCommand) -> ExecutionResult:
        ...


class MockExecutor:
    def run(self, command: PreparedCommand) -> ExecutionResult:
        stdout = [
            f"MOCK MODE: {command.title}",
            "No real command was executed.",
            "Command preview:",
            " ".join(command.argv),
        ]
        return ExecutionResult(0, "\n".join(stdout), "", command.argv, "mock")


class LocalExecutor:
    def run(self, command: PreparedCommand) -> ExecutionResult:
        return self.run_argv(command.argv, command.env, command.cwd)

    def run_argv(
        self,
        argv: list[str],
        command_env: tuple[str, ...] = (),
        cwd: str = "",
    ) -> ExecutionResult:
        env = os.environ.copy()
        for item in command_env:
            key, _, value = item.partition("=")
            env[key] = value
        try:
            proc = subprocess.run(
                argv,
                cwd=cwd or None,
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except FileNotFoundError:
            message = f"Executable not found: {argv[0]}"
            return ExecutionResult(
                127, "", message, argv, "local", classify_ssh_error(message)
            )
        except subprocess.TimeoutExpired:
            message = "Local command timed out."
            return ExecutionResult(
                124, "", message, argv, "local", classify_ssh_error(message)
            )
        return ExecutionResult(proc.returncode, proc.stdout, proc.stderr, argv, "local")


@dataclass(frozen=True)
class SshConnection:
    host: str
    user: str = "root"
    port: int = 22
    auth_mode: str = "ssh_config"
    key_path: str = ""
    password: str = ""


def build_ssh_invocation(
    connection: SshConnection, remote_argv: list[str]
) -> tuple[list[str], dict[str, str], list[str]]:
    if not connection.host:
        raise ValueError("SSH Host 不能为空")
    if not 1 <= connection.port <= 65535:
        raise ValueError("SSH 端口必须在 1 到 65535 之间")

    remote_command = " ".join(shell_quote(part) for part in remote_argv)
    ssh = [
        "ssh",
        "-p",
        str(connection.port),
        "-o",
        "ConnectTimeout=10",
    ]
    environment: dict[str, str] = {}

    if connection.auth_mode == "private_key":
        if not connection.key_path:
            raise ValueError("私钥模式需要填写私钥路径")
        ssh.extend(["-o", "BatchMode=yes", "-i", connection.key_path])
    elif connection.auth_mode == "password":
        raise ValueError("密码模式由 Paramiko 执行")
    elif connection.auth_mode == "ssh_config":
        ssh.extend(["-o", "BatchMode=yes"])
    else:
        raise ValueError("不支持的 SSH 认证方式")

    argv = [*ssh, f"{connection.user}@{connection.host}", remote_command]
    return argv, environment, list(argv)


def classify_ssh_error(stderr: str) -> dict[str, str]:
    message = stderr.lower()
    if "host key verification failed" in message or "remote host identification has changed" in message:
        return {
            "code": "host_key_failed",
            "message": "SSH 主机身份验证失败。",
            "recovery": "核对服务器 SSH 指纹，再更新应用可读取的 known_hosts；不要关闭主机指纹检查。",
        }
    if "identity file" in message and "not accessible" in message:
        return {
            "code": "key_not_found",
            "message": "SSH 私钥文件无法读取。",
            "recovery": "检查容器内私钥路径，并确认密钥目录已只读挂载到容器。",
        }
    if "permission denied" in message or "authentication failed" in message:
        return {
            "code": "authentication_failed",
            "message": "SSH 认证失败，请检查用户名和认证凭据。",
            "recovery": "确认用户、密码或私钥正确，并确认该账户允许 SSH 登录。",
        }
    if "connection timed out" in message or "command timed out" in message:
        return {
            "code": "connection_timeout",
            "message": "SSH 连接超时。",
            "recovery": "检查主机地址、端口、防火墙和 Docker 到宿主机的网络连通性。",
        }
    if "connection refused" in message:
        return {
            "code": "connection_refused",
            "message": "SSH 连接被拒绝。",
            "recovery": "确认 SSH 服务正在运行，并检查填写的端口。",
        }
    if "could not resolve hostname" in message or "no route to host" in message:
        return {
            "code": "host_unreachable",
            "message": "无法访问 SSH 主机。",
            "recovery": "检查主机名或 IP 地址、DNS 和网络路由。",
        }
    if "command not found" in message or "not found" in message and "executable" not in message:
        return {
            "code": "remote_command_missing",
            "message": "远程系统缺少所需命令。",
            "recovery": "在远程主机安装对应工具，并确认 SSH 用户的 PATH 可以找到该命令。",
        }
    if "executable not found" in message:
        return {
            "code": "client_missing",
            "message": "缺少 SSH 客户端组件。",
            "recovery": "私钥或 SSH 配置模式需要系统 ssh；密码模式需要 Paramiko。",
        }
    return {
        "code": "ssh_failed",
        "message": "SSH 命令执行失败。",
        "recovery": "查看错误详情，检查连接设置及远程账户权限。",
    }


class SshExecutor:
    def __init__(self, connection: SshConnection, password_runner=None):
        self.connection = connection
        self.password_runner = password_runner

    def run(self, command: PreparedCommand) -> ExecutionResult:
        remote_argv = ["env", *command.env, *command.argv] if command.env else command.argv
        return self.run_argv(remote_argv)

    def run_argv(
        self,
        remote_argv: list[str],
        command_env: tuple[str, ...] = (),
        cwd: str = "",
    ) -> ExecutionResult:
        if command_env:
            remote_argv = ["env", *command_env, *remote_argv]

        if self.connection.auth_mode == "password":
            validation_error = validate_password_connection(self.connection)
            if validation_error:
                return validation_error
            runner = self.password_runner
            if runner is None:
                from .paramiko_transport import run_paramiko_command

                runner = run_paramiko_command
            remote_command = " ".join(shell_quote(part) for part in remote_argv)
            return runner(self.connection, remote_command)

        try:
            ssh_argv, secret_env, display_argv = build_ssh_invocation(
                self.connection, remote_argv
            )
        except ValueError as exc:
            return ExecutionResult(
                2,
                "",
                str(exc),
                [],
                "ssh",
                {"code": "invalid_connection", "message": str(exc), "recovery": "检查 SSH 连接配置。"},
            )

        environment = os.environ.copy()
        environment.update(secret_env)
        try:
            proc = subprocess.run(
                ssh_argv,
                env=environment,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
                check=False,
            )
        except FileNotFoundError as exc:
            message = f"Executable not found: {exc.filename or ssh_argv[0]}"
            return ExecutionResult(
                127,
                "",
                message,
                display_argv,
                "ssh",
                classify_ssh_error(message),
            )
        except subprocess.TimeoutExpired:
            message = "SSH command timed out."
            return ExecutionResult(
                124,
                "",
                message,
                display_argv,
                "ssh",
                classify_ssh_error(message),
            )

        error = classify_ssh_error(proc.stderr) if proc.returncode else None
        return ExecutionResult(
            proc.returncode,
            proc.stdout,
            proc.stderr,
            display_argv,
            "ssh",
            error,
        )


def validate_password_connection(connection: SshConnection) -> ExecutionResult | None:
    message = ""
    if not connection.host:
        message = "SSH Host 不能为空"
    elif not 1 <= connection.port <= 65535:
        message = "SSH 端口必须在 1 到 65535 之间"
    elif not connection.password:
        message = "密码模式需要输入 SSH 密码"

    if not message:
        return None
    return ExecutionResult(
        2,
        "",
        message,
        [],
        "ssh",
        {
            "code": "invalid_connection",
            "message": message,
            "recovery": "检查 SSH 连接配置。",
        },
    )


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"
