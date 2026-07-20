"""
WorkOps SSH Adapter Errors — SSH 错误模型
Sprint022: SSH Adapter Read-Only Foundation

固定安全消息。
禁止 str(exc)、禁止原始异常传播、禁止保留 traceback cause。
"""


class SSHAdapterError(Exception):
    """SSH Adapter 错误基类"""
    pass


class SSHConfigurationError(SSHAdapterError):
    """配置错误"""
    pass


class SSHAuthenticationError(SSHAdapterError):
    """认证失败"""
    pass


class SSHHostKeyError(SSHAdapterError):
    """主机密钥验证失败"""
    pass


class SSHConnectionError(SSHAdapterError):
    """连接失败"""
    pass


class SSHTimeoutError(SSHAdapterError):
    """连接或查询超时"""
    pass


class SSHQueryNotAllowedError(SSHAdapterError):
    """查询不在白名单中"""
    pass


class SSHQueryExecutionError(SSHAdapterError):
    """查询执行失败"""
    pass
