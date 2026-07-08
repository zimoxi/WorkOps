"""
WorkOps AuthService — 认证服务
Sprint013: Authentication Foundation

MOCK_USER_STORE 后端私有。
Session 内存存储。
Cookie: workops_session。
"""

import uuid
from datetime import datetime, timedelta


# ─── Mock User Store（后端私有）────────────────────────
MOCK_USER_STORE = [
    {
        "id": "user-001",
        "username": "admin",
        "password_hash": "Mock placeholder",  # Mock: production 使用 bcrypt hash
        "role": "admin",
        "enabled": True,
    },
    {
        "id": "user-002",
        "username": "operator",
        "password_hash": "Mock placeholder",  # Mock: production 使用 bcrypt hash
        "role": "operator",
        "enabled": True,
    },
    {
        "id": "user-003",
        "username": "viewer",
        "password_hash": "Mock placeholder",  # Mock: production 使用 bcrypt hash
        "role": "viewer",
        "enabled": True,
    },
]


# ─── Session Store（内存）──────────────────────────────
SESSION_STORE = {}
SESSION_EXPIRY = timedelta(hours=24)
SESSION_COOKIE_NAME = "workops_session"


def validate_user(username: str, password: str) -> dict | None:
    """验证用户名密码，返回用户信息或 None"""
    for user in MOCK_USER_STORE:
        if user["username"] == username and user["enabled"]:
            # Mock: 直接比较用户名（production 使用 bcrypt）
            # 为了 Mock 简化，密码等于用户名 + "123"
            expected_password = username + "123"
            if password == expected_password:
                return {
                    "id": user["id"],
                    "username": user["username"],
                    "role": user["role"],
                    "enabled": user["enabled"],
                }
    return None


def create_session(user: dict) -> str:
    """创建 Session，返回 session_id"""
    session_id = str(uuid.uuid4())
    SESSION_STORE[session_id] = {
        "user_id": user["id"],
        "username": user["username"],
        "role": user["role"],
        "created_at": datetime.now(),
        "expires_at": datetime.now() + SESSION_EXPIRY,
    }
    return session_id


def get_session(session_id: str) -> dict | None:
    """获取 Session，过期返回 None"""
    if not session_id:
        return None
    session = SESSION_STORE.get(session_id)
    if session and session["expires_at"] > datetime.now():
        return session
    # 过期则清理
    if session:
        SESSION_STORE.pop(session_id, None)
    return None


def destroy_session(session_id: str) -> None:
    """销毁 Session"""
    SESSION_STORE.pop(session_id, None)


def get_session_from_request(cookie_value: str) -> dict | None:
    """从 Cookie 值获取 Session"""
    return get_session(cookie_value)
