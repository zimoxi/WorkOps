"""
WorkOps Paramiko Read-Only Client — 受控 SSH 客户端
Sprint022: SSH Adapter Read-Only Foundation

双通道有界读取。安全异常映射。
禁止 load_system_host_keys、AutoAddPolicy、save_host_keys。
禁止 subprocess、系统 ssh.exe、SFTP/SCP/Tunnel。
"""

import select
import socket
import time

from .ssh_client_protocol import SSHClientProtocol
from .ssh_errors import (
    SSHAuthenticationError,
    SSHConnectionError,
    SSHHostKeyError,
    SSHQueryExecutionError,
    SSHQueryNotAllowedError,
    SSHTimeoutError,
)
from .ssh_models import QUERY_REGISTRY, SSHClientOutput, compute_host_fingerprint


class ParamikoReadOnlyClient(SSHClientProtocol):
    """
    Paramiko 只读客户端。
    通过构造函数注入 paramiko 模块以便测试。
    """

    def __init__(self, paramiko_module=None):
        if paramiko_module is not None:
            self._paramiko = paramiko_module
        else:
            import paramiko as _p
            self._paramiko = _p
        self._client = None

    # ------------------------------------------------------------------
    # connect
    # ------------------------------------------------------------------
    def connect(self, config, username, password):
        client = self._paramiko.SSHClient()
        client.load_host_keys(config.known_hosts_path)
        client.set_missing_host_key_policy(self._paramiko.RejectPolicy())
        try:
            client.connect(
                hostname=config.host,
                port=config.port,
                username=username,
                password=password,
                allow_agent=False,
                look_for_keys=False,
                timeout=config.connect_timeout,
                auth_timeout=config.connect_timeout,
                banner_timeout=config.connect_timeout,
            )
            self._client = client
        except self._paramiko.AuthenticationException:
            try:
                client.close()
            except Exception:
                pass
            raise SSHAuthenticationError("Authentication failed") from None
        except self._paramiko.BadHostKeyException:
            try:
                client.close()
            except Exception:
                pass
            raise SSHHostKeyError("Host key verification failed") from None
        except self._paramiko.NoValidConnectionsError:
            try:
                client.close()
            except Exception:
                pass
            raise SSHConnectionError("Connection failed") from None
        except (socket.timeout, TimeoutError):
            try:
                client.close()
            except Exception:
                pass
            raise SSHTimeoutError("Connection timed out") from None
        except self._paramiko.SSHException:
            try:
                client.close()
            except Exception:
                pass
            raise SSHConnectionError("SSH error") from None
        except Exception:
            try:
                client.close()
            except Exception:
                pass
            raise SSHConnectionError("Unexpected connection error") from None

    # ------------------------------------------------------------------
    # run_query
    # ------------------------------------------------------------------
    def run_query(self, query_id, timeout, max_output_bytes):
        query_def = QUERY_REGISTRY.get(query_id)
        if query_def is None:
            raise SSHQueryNotAllowedError("SSH query is not allowed")
        try:
            stdin, stdout_ch, stderr_ch = self._client.exec_command(
                query_def.command, timeout=timeout
            )
            stdin.close()
            channel = stdout_ch.channel
            try:
                output = self._read_dual_channel(channel, max_output_bytes, timeout)
            finally:
                try:
                    channel.close()
                except Exception:
                    pass
            return output
        except (SSHTimeoutError, SSHQueryNotAllowedError, SSHQueryExecutionError):
            raise
        except (socket.timeout, TimeoutError):
            raise SSHTimeoutError("Query timed out") from None
        except self._paramiko.SSHException:
            raise SSHQueryExecutionError("Query execution failed") from None
        except Exception:
            raise SSHQueryExecutionError("Query execution failed") from None

    # ------------------------------------------------------------------
    # 双通道有界读取
    # ------------------------------------------------------------------
    def _read_dual_channel(self, channel, max_bytes, timeout):
        """
        同一个 Paramiko Channel。
        recv_ready()/recv()  recv_stderr_ready()/recv_stderr()
        exit_status_ready()  time.monotonic() deadline
        select.select 有界等待
        stdout/stderr 分别最多 max_bytes
        超限内容不再保存
        超时关闭 Channel
        Channel 在 finally 中关闭
        禁止 .read()
        禁止无限排空
        只有 exit_status_ready 后调用 recv_exit_status
        """
        deadline = time.monotonic() + timeout
        stdout_chunks = []
        stderr_chunks = []
        stdout_total = 0
        stderr_total = 0
        stdout_truncated = False
        stderr_truncated = False
        exit_code = None

        try:
            while True:
                now = time.monotonic()
                if now >= deadline:
                    raise SSHTimeoutError("Query timed out")
                remaining = deadline - now
                wait_sec = min(0.1, remaining)

                try:
                    rlist, _, _ = select.select([channel], [], [], wait_sec)
                except Exception:
                    pass

                if exit_code is None and channel.exit_status_ready():
                    exit_code = channel.recv_exit_status()

                # stdout
                if channel.recv_ready():
                    chunk = channel.recv(4096)
                    if not chunk:
                        if exit_code is not None:
                            break
                        # EOF without exit code — wait a bit
                        time.sleep(0.01)
                        continue
                    if stdout_total < max_bytes:
                        allowed = max_bytes - stdout_total
                        if len(chunk) > allowed:
                            stdout_chunks.append(chunk[:allowed])
                            stdout_truncated = True
                            stdout_total = max_bytes
                        else:
                            stdout_chunks.append(chunk)
                            stdout_total += len(chunk)
                    else:
                        stdout_truncated = True

                # stderr
                if channel.recv_stderr_ready():
                    chunk = channel.recv_stderr(4096)
                    if chunk:
                        if stderr_total < max_bytes:
                            allowed = max_bytes - stderr_total
                            if len(chunk) > allowed:
                                stderr_chunks.append(chunk[:allowed])
                                stderr_truncated = True
                                stderr_total = max_bytes
                            else:
                                stderr_chunks.append(chunk)
                                stderr_total += len(chunk)
                        else:
                            stderr_truncated = True

                # 两者都结束
                if exit_code is not None:
                    if not channel.recv_ready() and not channel.recv_stderr_ready():
                        break

        except SSHTimeoutError:
            raise
        except Exception:
            raise SSHQueryExecutionError("Query execution failed") from None

        if exit_code is None:
            exit_code = -1

        return SSHClientOutput(
            exit_code=exit_code,
            stdout=b"".join(stdout_chunks),
            stderr=b"".join(stderr_chunks),
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
        )

    # ------------------------------------------------------------------
    # get_host_fingerprint
    # ------------------------------------------------------------------
    def get_host_fingerprint(self):
        try:
            transport = self._client.get_transport()
            key = transport.get_remote_server_key()
            host, port = transport.getpeername()
            return compute_host_fingerprint(key, host, port)
        except Exception:
            raise SSHConnectionError("Failed to get fingerprint") from None

    # ------------------------------------------------------------------
    # close
    # ------------------------------------------------------------------
    def close(self):
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
