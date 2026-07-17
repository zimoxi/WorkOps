"""
WorkOps Redaction Utility — 脱敏工具
Sprint021: Credential and Secret Management

纯函数，不修改原始对象
支持大小写、snake_case、camelCase、Header、Query
支持嵌套 dict/list/tuple
循环引用安全
"""

import re
from typing import Any

from .secret_value import SecretValue

# 敏感字段名（小写）
REDACTED_FIELDS = frozenset({
    "password", "passwd", "passphrase", "secret", "secret_ref",
    "token", "access_token", "refresh_token", "private_key",
    "authorization", "proxy_authorization", "cookie", "set_cookie",
    "session_id", "api_key", "api_secret", "client_secret",
    "bearer_token", "ssh_password",
})

REDACTED = "[REDACTED]"
CIRCULAR = "[CIRCULAR]"
UNSUPPORTED = "[UNSUPPORTED_OBJECT]"


def _normalize_key(key: str) -> str:
    """标准化键名：camelCase/snake_case/kebab-case -> 小写"""
    if not isinstance(key, str):
        return str(key).lower()

    # 处理 camelCase
    # accessToken -> access_token
    s1 = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', key)
    s2 = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s1)

    # 处理 kebab-case
    s3 = s2.replace('-', '_')

    # 转小写
    return s3.lower()


def _is_sensitive_key(key: str) -> bool:
    """检查键名是否敏感"""
    normalized = _normalize_key(key)
    return normalized in REDACTED_FIELDS


def redact(value: Any, _seen: set = None) -> Any:
    """
    递归脱敏，不修改输入
    
    Args:
        value: 要脱敏的值
        _seen: 已访问对象集合（用于循环引用检测）
    
    Returns:
        脱敏后的新对象
    """
    if _seen is None:
        _seen = set()

    # 循环引用检测
    value_id = id(value)
    if value_id in _seen:
        return CIRCULAR

    # SecretValue 直接脱敏
    if isinstance(value, SecretValue):
        return REDACTED

    # 字符串
    if isinstance(value, str):
        return value

    # 字典
    if isinstance(value, dict):
        _seen.add(value_id)
        result = {}
        for k, v in value.items():
            if _is_sensitive_key(str(k)):
                result[k] = REDACTED
            else:
                result[k] = redact(v, _seen)
        _seen.discard(value_id)
        return result

    # 列表
    if isinstance(value, list):
        _seen.add(value_id)
        result = [redact(item, _seen) for item in value]
        _seen.discard(value_id)
        return result

    # 元组
    if isinstance(value, tuple):
        _seen.add(value_id)
        result = tuple(redact(item, _seen) for item in value)
        _seen.discard(value_id)
        return result

    # 集合
    if isinstance(value, (set, frozenset)):
        _seen.add(value_id)
        result = [redact(item, _seen) for item in value]
        _seen.discard(value_id)
        return result

    # CredentialMetadata
    if hasattr(value, 'to_safe_dict') and callable(value.to_safe_dict):
        try:
            return value.to_safe_dict()
        except Exception:
            return UNSUPPORTED

    # 其他不可迭代对象
    if isinstance(value, (int, float, bool, type(None))):
        return value

    # 未知对象
    return UNSUPPORTED


def redact_text(text: str) -> str:
    """
    自由文本脱敏
    
    不是完整 DLP 系统。
    无字段名、无上下文的任意 Secret 无法保证识别。
    
    Args:
        text: 要脱敏的文本
    
    Returns:
        脱敏后的文本
    """
    if not isinstance(text, str):
        return str(text)

    result = text

    # password=value 或 password: value
    result = re.sub(
        r'((?:password|passwd|passphrase|secret|token|api_key|api_secret|client_secret|ssh_password|bearer_token)\s*[=:]\s*)(\S+)',
        r'\1' + REDACTED,
        result,
        flags=re.IGNORECASE
    )

    # Authorization: Bearer ***
    result = re.sub(
        r'(Authorization:\s*Bearer\s+)(\S+)',
        r'\1' + REDACTED,
        result,
        flags=re.IGNORECASE
    )

    # Cookie: ...
    result = re.sub(
        r'(Cookie:\s*)(.+)',
        r'\1' + REDACTED,
        result,
        flags=re.IGNORECASE
    )

    # Set-Cookie: ...
    result = re.sub(
        r'(Set-Cookie:\s*)(.+)',
        r'\1' + REDACTED,
        result,
        flags=re.IGNORECASE
    )

    return result
