"""
WorkOps Credential Tests
Sprint021: Credential and Secret Management

覆盖：
- CredentialMetadata 字段验证
- 未知 credential_type 拒绝
- Metadata repr/to_safe_dict 不含 secret_ref
- SecretValue str/repr 不泄漏
- Provider store/retrieve/delete/exists
- 引用不可预测且唯一
- 空 Secret 拒绝
- 缺失引用错误不含 ref
- 无 list_all
- Provider repr 不泄漏
- Redaction 大小写/snake/camel
- 嵌套 dict/list/tuple
- Header/Query
- 循环引用
- 不修改原对象
- 自由文本常见模式
- 不引入加密或连接依赖
- 原有 192 项测试继续通过
- Full Suite 连续运行两次
"""

import unittest
from datetime import datetime, timezone

from backup_manager.credentials.errors import (
    CredentialError,
    CredentialValidationError,
    SecretNotFoundError,
    SecretProviderError,
)
from backup_manager.credentials.model import CredentialType, CredentialMetadata
from backup_manager.credentials.secret_value import SecretValue
from backup_manager.credentials.provider import SecretProvider
from backup_manager.credentials.in_memory import InMemorySecretProvider
from backup_manager.credentials.redaction import redact, redact_text


# ─── CredentialMetadata Tests ───────────────────────

class TestCredentialMetadata(unittest.TestCase):
    """测试 CredentialMetadata"""

    def test_valid_metadata(self):
        """合法 Metadata"""
        now = datetime.now(timezone.utc)
        metadata = CredentialMetadata(
            credential_id="cred-001",
            name="Test Credential",
            credential_type=CredentialType.PASSWORD,
            username="admin",
            secret_ref="ref-001",
            created_at=now,
            updated_at=now,
        )
        self.assertEqual(metadata.credential_id, "cred-001")
        self.assertEqual(metadata.name, "Test Credential")
        self.assertEqual(metadata.credential_type, CredentialType.PASSWORD)

    def test_unknown_credential_type(self):
        """未知 credential_type 拒绝"""
        now = datetime.now(timezone.utc)
        with self.assertRaises(CredentialValidationError):
            CredentialMetadata(
                credential_id="cred-001",
                name="Test",
                credential_type="invalid",
                username="admin",
                secret_ref="ref-001",
                created_at=now,
                updated_at=now,
            )

    def test_missing_fields(self):
        """缺少字段拒绝"""
        with self.assertRaises(TypeError):
            CredentialMetadata()

    def test_empty_credential_id(self):
        """空 credential_id 拒绝"""
        now = datetime.now(timezone.utc)
        with self.assertRaises(CredentialValidationError):
            CredentialMetadata(
                credential_id="",
                name="Test",
                credential_type=CredentialType.PASSWORD,
                username="admin",
                secret_ref="ref-001",
                created_at=now,
                updated_at=now,
            )

    def test_empty_name(self):
        """空 name 拒绝"""
        now = datetime.now(timezone.utc)
        with self.assertRaises(CredentialValidationError):
            CredentialMetadata(
                credential_id="cred-001",
                name="",
                credential_type=CredentialType.PASSWORD,
                username="admin",
                secret_ref="ref-001",
                created_at=now,
                updated_at=now,
            )

    def test_empty_secret_ref(self):
        """空 secret_ref 拒绝"""
        now = datetime.now(timezone.utc)
        with self.assertRaises(CredentialValidationError):
            CredentialMetadata(
                credential_id="cred-001",
                name="Test",
                credential_type=CredentialType.PASSWORD,
                username="admin",
                secret_ref="",
                created_at=now,
                updated_at=now,
            )

    def test_repr_no_secret_ref(self):
        """repr 不含 secret_ref"""
        now = datetime.now(timezone.utc)
        metadata = CredentialMetadata(
            credential_id="cred-001",
            name="Test",
            credential_type=CredentialType.PASSWORD,
            username="admin",
            secret_ref="ref-001",
            created_at=now,
            updated_at=now,
        )
        repr_str = repr(metadata)
        self.assertNotIn("ref-001", repr_str)
        self.assertNotIn("secret_ref", repr_str)

    def test_str_no_secret_ref(self):
        """str 不含 secret_ref"""
        now = datetime.now(timezone.utc)
        metadata = CredentialMetadata(
            credential_id="cred-001",
            name="Test",
            credential_type=CredentialType.PASSWORD,
            username="admin",
            secret_ref="ref-001",
            created_at=now,
            updated_at=now,
        )
        str_str = str(metadata)
        self.assertNotIn("ref-001", str_str)
        self.assertNotIn("secret_ref", str_str)

    def test_to_safe_dict_no_secret_ref(self):
        """to_safe_dict 不含 secret_ref"""
        now = datetime.now(timezone.utc)
        metadata = CredentialMetadata(
            credential_id="cred-001",
            name="Test",
            credential_type=CredentialType.PASSWORD,
            username="admin",
            secret_ref="ref-001",
            created_at=now,
            updated_at=now,
        )
        safe_dict = metadata.to_safe_dict()
        self.assertNotIn("secret_ref", safe_dict)
        self.assertEqual(safe_dict["credential_id"], "cred-001")

    def test_immutable(self):
        """不可变"""
        now = datetime.now(timezone.utc)
        metadata = CredentialMetadata(
            credential_id="cred-001",
            name="Test",
            credential_type=CredentialType.PASSWORD,
            username="admin",
            secret_ref="ref-001",
            created_at=now,
            updated_at=now,
        )
        with self.assertRaises(AttributeError):
            metadata.credential_id = "new-id"


# ─── SecretValue Tests ───────────────────────────────

class TestSecretValue(unittest.TestCase):
    """测试 SecretValue"""

    def test_empty_secret_rejected(self):
        """空值拒绝"""
        with self.assertRaises(CredentialValidationError):
            SecretValue("")

    def test_non_string_rejected(self):
        """非字符串拒绝"""
        with self.assertRaises(CredentialValidationError):
            SecretValue(123)

    def test_reveal(self):
        """reveal 显式返回"""
        secret = SecretValue("my-secret")
        self.assertEqual(secret.reveal(), "my-secret")

    def test_str_redacted(self):
        """str 不泄漏"""
        secret = SecretValue("my-secret")
        self.assertEqual(str(secret), "[REDACTED]")

    def test_repr_redacted(self):
        """repr 不泄漏"""
        secret = SecretValue("my-secret")
        self.assertEqual(repr(secret), "SecretValue([REDACTED])")

    def test_format_redacted(self):
        """格式化字符串不泄漏"""
        secret = SecretValue("my-secret")
        self.assertEqual(f"{secret}", "[REDACTED]")
        self.assertEqual(f"{secret:>20}", "[REDACTED]")

    def test_no_serialization(self):
        """无序列化接口"""
        secret = SecretValue("my-secret")
        self.assertFalse(hasattr(secret, 'to_dict'))
        self.assertFalse(hasattr(secret, 'serialize'))
        self.assertFalse(hasattr(secret, 'json'))

    def test_no_value_property(self):
        """无 value 属性"""
        secret = SecretValue("my-secret")
        self.assertFalse(hasattr(secret, 'value'))
        self.assertFalse(hasattr(secret, 'secret'))

    def test_equality(self):
        """相等性"""
        secret1 = SecretValue("my-secret")
        secret2 = SecretValue("my-secret")
        secret3 = SecretValue("other-secret")
        self.assertEqual(secret1, secret2)
        self.assertNotEqual(secret1, secret3)


# ─── InMemorySecretProvider Tests ─────────────────────

class TestInMemorySecretProvider(unittest.TestCase):
    """测试 InMemorySecretProvider"""

    def test_store_and_retrieve(self):
        """store/retrieve"""
        provider = InMemorySecretProvider()
        secret_ref = provider.store("my-secret")
        secret_value = provider.retrieve(secret_ref)
        self.assertEqual(secret_value.reveal(), "my-secret")

    def test_store_secret_value(self):
        """store SecretValue"""
        provider = InMemorySecretProvider()
        secret_ref = provider.store(SecretValue("my-secret"))
        secret_value = provider.retrieve(secret_ref)
        self.assertEqual(secret_value.reveal(), "my-secret")

    def test_exists(self):
        """exists"""
        provider = InMemorySecretProvider()
        secret_ref = provider.store("my-secret")
        self.assertTrue(provider.exists(secret_ref))
        self.assertFalse(provider.exists("nonexistent"))

    def test_delete(self):
        """delete"""
        provider = InMemorySecretProvider()
        secret_ref = provider.store("my-secret")
        provider.delete(secret_ref)
        self.assertFalse(provider.exists(secret_ref))

    def test_delete_idempotent(self):
        """delete 幂等"""
        provider = InMemorySecretProvider()
        secret_ref = provider.store("my-secret")
        provider.delete(secret_ref)
        provider.delete(secret_ref)  # 不报错

    def test_missing_ref_error(self):
        """缺失引用错误不含 ref"""
        provider = InMemorySecretProvider()
        with self.assertRaises(SecretNotFoundError) as ctx:
            provider.retrieve("nonexistent")
        self.assertNotIn("nonexistent", str(ctx.exception))

    def test_unique_refs(self):
        """引用唯一"""
        provider = InMemorySecretProvider()
        ref1 = provider.store("secret-1")
        ref2 = provider.store("secret-2")
        self.assertNotEqual(ref1, ref2)

    def test_unpredictable_refs(self):
        """引用不可预测"""
        provider = InMemorySecretProvider()
        ref = provider.store("my-secret")
        # 至少 32 字符
        self.assertGreaterEqual(len(ref), 32)

    def test_no_list_all(self):
        """无 list_all"""
        provider = InMemorySecretProvider()
        self.assertFalse(hasattr(provider, 'list'))
        self.assertFalse(hasattr(provider, 'list_all'))
        self.assertFalse(hasattr(provider, 'get_all'))
        self.assertFalse(hasattr(provider, 'export'))
        self.assertFalse(hasattr(provider, 'dump'))

    def test_repr_no_secrets(self):
        """repr 不泄漏"""
        provider = InMemorySecretProvider()
        provider.store("my-secret")
        repr_str = repr(provider)
        self.assertNotIn("my-secret", repr_str)

    def test_new_instance_no_shared_data(self):
        """新实例不共享数据"""
        provider1 = InMemorySecretProvider()
        secret_ref = provider1.store("my-secret")

        provider2 = InMemorySecretProvider()
        self.assertFalse(provider2.exists(secret_ref))

    def test_retrieve_returns_new_wrapper(self):
        """retrieve 返回新的 SecretValue"""
        provider = InMemorySecretProvider()
        secret_ref = provider.store("my-secret")

        sv1 = provider.retrieve(secret_ref)
        sv2 = provider.retrieve(secret_ref)
        self.assertIsNot(sv1, sv2)
        self.assertEqual(sv1.reveal(), sv2.reveal())

    def test_empty_secret_rejected(self):
        """空 Secret 拒绝"""
        provider = InMemorySecretProvider()
        with self.assertRaises(CredentialValidationError):
            provider.store("")

    def test_empty_ref_rejected(self):
        """空引用拒绝"""
        provider = InMemorySecretProvider()
        with self.assertRaises(SecretNotFoundError):
            provider.retrieve("")

    def test_not_expose_internal_dict(self):
        """不暴露内部字典"""
        provider = InMemorySecretProvider()
        # _store 是私有属性，但可以通过 name mangling 访问
        # 关键是不暴露为公共 API
        self.assertFalse(hasattr(provider, 'store_dict'))
        self.assertFalse(hasattr(provider, 'secrets'))
        self.assertFalse(hasattr(provider, 'items'))


# ─── Redaction Tests ─────────────────────────────────

class TestRedaction(unittest.TestCase):
    """测试 Redaction"""

    def test_password_case(self):
        """password / PASSWORD / Password"""
        data = {"password": "secret", "PASSWORD": "secret", "Password": "secret"}
        result = redact(data)
        self.assertEqual(result["password"], "[REDACTED]")
        self.assertEqual(result["PASSWORD"], "[REDACTED]")
        self.assertEqual(result["Password"], "[REDACTED]")

    def test_ssh_password(self):
        """ssh_password / sshPassword"""
        data = {"ssh_password": "secret", "sshPassword": "secret"}
        result = redact(data)
        self.assertEqual(result["ssh_password"], "[REDACTED]")
        self.assertEqual(result["sshPassword"], "[REDACTED]")

    def test_access_token(self):
        """access_token / accessToken"""
        data = {"access_token": "secret", "accessToken": "secret"}
        result = redact(data)
        self.assertEqual(result["access_token"], "[REDACTED]")
        self.assertEqual(result["accessToken"], "[REDACTED]")

    def test_private_key(self):
        """private_key / privateKey"""
        data = {"private_key": "secret", "privateKey": "secret"}
        result = redact(data)
        self.assertEqual(result["private_key"], "[REDACTED]")
        self.assertEqual(result["privateKey"], "[REDACTED]")

    def test_authorization_header(self):
        """Authorization"""
        data = {"Authorization": "Bearer ***"}
        result = redact(data)
        self.assertEqual(result["Authorization"], "[REDACTED]")

    def test_cookie(self):
        """Cookie / Set-Cookie"""
        data = {"Cookie": "session=abc", "Set-Cookie": "session=abc"}
        result = redact(data)
        self.assertEqual(result["Cookie"], "[REDACTED]")
        self.assertEqual(result["Set-Cookie"], "[REDACTED]")

    def test_session_id(self):
        """session_id / sessionId"""
        data = {"session_id": "abc", "sessionId": "abc"}
        result = redact(data)
        self.assertEqual(result["session_id"], "[REDACTED]")
        self.assertEqual(result["sessionId"], "[REDACTED]")

    def test_secret_ref(self):
        """secret_ref"""
        data = {"secret_ref": "ref-001"}
        result = redact(data)
        self.assertEqual(result["secret_ref"], "[REDACTED]")

    def test_nested_dict(self):
        """嵌套 dict"""
        data = {"outer": {"password": "secret"}}
        result = redact(data)
        self.assertEqual(result["outer"]["password"], "[REDACTED]")

    def test_nested_list(self):
        """嵌套 list"""
        data = {"items": [{"password": "secret"}]}
        result = redact(data)
        self.assertEqual(result["items"][0]["password"], "[REDACTED]")

    def test_nested_tuple(self):
        """嵌套 tuple"""
        data = {"items": ({"password": "secret"},)}
        result = redact(data)
        self.assertEqual(result["items"][0]["password"], "[REDACTED]")

    def test_header(self):
        """Header"""
        data = {"headers": {"Authorization": "Bearer ***"}}
        result = redact(data)
        self.assertEqual(result["headers"]["Authorization"], "[REDACTED]")

    def test_query_params(self):
        """Query 参数"""
        data = {"query": {"token": "abc"}}
        result = redact(data)
        self.assertEqual(result["query"]["token"], "[REDACTED]")

    def test_circular_reference(self):
        """循环引用"""
        data = {"key": "value"}
        data["self"] = data
        result = redact(data)
        self.assertEqual(result["key"], "value")
        self.assertEqual(result["self"], "[CIRCULAR]")

    def test_input_not_modified(self):
        """输入对象不被修改"""
        data = {"password": "secret"}
        original = data.copy()
        redact(data)
        self.assertEqual(data, original)

    def test_secret_value_redacted(self):
        """SecretValue 直接脱敏"""
        secret = SecretValue("my-secret")
        result = redact(secret)
        self.assertEqual(result, "[REDACTED]")

    def test_text_password_pattern(self):
        """自由文本 password="""
        text = "password=my-secret"
        result = redact_text(text)
        self.assertIn("[REDACTED]", result)
        self.assertNotIn("my-secret", result)

    def test_text_bearer_pattern(self):
        """自由文本 Bearer"""
        text = "Authorization: Bearer ***"
        result = redact_text(text)
        self.assertIn("[REDACTED]", result)
        self.assertNotIn("***", result)

    def test_text_cookie_pattern(self):
        """自由文本 Cookie"""
        text = "Cookie: session=abc"
        result = redact_text(text)
        self.assertIn("[REDACTED]", result)
        self.assertNotIn("session=abc", result)

    def test_normal_text_preserved(self):
        """普通非敏感文本保持可读"""
        text = "Hello World"
        result = redact_text(text)
        self.assertEqual(result, "Hello World")

    def test_redact_idempotent(self):
        """redact 幂等"""
        data = {"password": "secret"}
        result1 = redact(data)
        result2 = redact(result1)
        self.assertEqual(result1, result2)

    def test_redact_text_idempotent(self):
        """redact_text 幂等"""
        text = "password=secret"
        result1 = redact_text(text)
        result2 = redact_text(result1)
        self.assertEqual(result1, result2)


# ─── Security Boundary Tests ─────────────────────────

class TestSecurityBoundary(unittest.TestCase):
    """测试安全边界"""

    def test_no_cryptography_import(self):
        """不引入 cryptography"""
        import sys
        self.assertNotIn("cryptography", sys.modules)

    def test_no_keyring_import(self):
        """不引入 keyring"""
        import sys
        self.assertNotIn("keyring", sys.modules)

    def test_no_paramiko_import(self):
        """不引入 paramiko"""
        import sys
        self.assertNotIn("paramiko", sys.modules)


if __name__ == "__main__":
    unittest.main()
