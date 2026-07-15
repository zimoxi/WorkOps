"""
WorkOps Connection Factory — 数据库连接
Sprint020: Persistence Foundation

每次 SQLite 操作后显式关闭连接
使用 contextmanager
不保留全局长期 connection
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def connect(db_path):
    """
    Context manager that opens and CLOSES the connection.
    
    - sqlite3.connect()
    - row_factory = sqlite3.Row
    - PRAGMA foreign_keys = ON
    - 成功时 commit
    - 异常时 rollback
    - finally close
    """
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
