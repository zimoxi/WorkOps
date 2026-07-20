"""
WorkOps AdapterFactory — Adapter 工厂方法
Sprint017: Device Adapter Foundation
Sprint022: 新增 ssh_readonly 类型
Sprint023: 注册到 AdapterRegistry

只暴露 create(adapter_type)
"""

from .mock_adapter import MockAdapter
from .ssh_adapter import SSHAdapter
from .winrm_adapter import WinRMAdapter
from .snmp_adapter import SNMPAdapter
from .errors import AdapterNotImplementedError


class AdapterFactory:
    """Adapter 工厂方法"""

    _adapters = {
        "mock": MockAdapter,
        "ssh": SSHAdapter,
        "winrm": WinRMAdapter,
        "snmp": SNMPAdapter,
    }

    @classmethod
    def create(cls, adapter_type: str, **kwargs):
        """
        创建 Adapter 实例

        Args:
            adapter_type: Adapter 类型 (mock, ssh, ssh_readonly, winrm, snmp)
            **kwargs: ssh_readonly 必需 credential_metadata, secret_provider;
                      可选 client_factory

        Returns:
            BaseAdapter: Adapter 实例

        Raises:
            AdapterNotImplementedError: 不支持的 Adapter 类型
            SSHConfigurationError: 配置错误
        """
        if adapter_type == "ssh_readonly":
            from .ssh_readonly_adapter import SSHReadOnlyAdapter
            from .ssh_errors import SSHConfigurationError

            required = {"credential_metadata", "secret_provider"}
            optional = {"client_factory"}
            allowed = required | optional
            unknown = set(kwargs.keys()) - allowed
            if unknown:
                raise SSHConfigurationError("Unknown kwargs for ssh_readonly")
            missing = required - set(kwargs.keys())
            if missing:
                raise SSHConfigurationError("Missing required kwargs for ssh_readonly")
            if "client_factory" in kwargs and not callable(kwargs["client_factory"]):
                raise SSHConfigurationError("client_factory must be callable")
            return SSHReadOnlyAdapter(**kwargs)

        # 非 ssh_readonly 类型携带 kwargs 时拒绝
        if kwargs:
            from .ssh_errors import SSHConfigurationError
            raise SSHConfigurationError("This adapter type does not accept kwargs")

        adapter_class = cls._adapters.get(adapter_type)
        if not adapter_class:
            raise AdapterNotImplementedError(f"Unknown adapter type: {adapter_type}")
        return adapter_class()

    @classmethod
    def register_to_registry(cls, registry) -> None:
        """
        注册内置 Adapter 到 AdapterRegistry。

        只注册 mock 和 ssh_readonly。
        """
        from .capabilities import AdapterCapability
        from .descriptor import AdapterDescriptor

        # Mock
        mock_desc = AdapterDescriptor(
            adapter_type="mock",
            capabilities=frozenset({AdapterCapability.STATUS_QUERY}),
            readonly=True,
        )
        registry.register(mock_desc, MockAdapter)

        # SSH ReadOnly
        from .ssh_readonly_adapter import SSHReadOnlyAdapter

        ssh_desc = AdapterDescriptor(
            adapter_type="ssh_readonly",
            capabilities=frozenset({
                AdapterCapability.STATUS_QUERY,
                AdapterCapability.SYSTEM_QUERY,
            }),
            readonly=True,
        )
        registry.register(ssh_desc, SSHReadOnlyAdapter)
