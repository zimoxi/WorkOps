"""
WorkOps Persistence Config — 配置
Sprint020: Persistence Foundation
"""

from .errors import PersistenceValidationError


class PersistenceConfig:
    """Persistence 配置"""

    VALID_MODES = ("mock", "database")

    def __init__(self, mode="mock", db_path=None, context=None):
        self.mode = mode
        self.db_path = db_path
        self.context = context
        self._validate()

    def _validate(self):
        if self.mode not in self.VALID_MODES:
            raise PersistenceValidationError(f"Invalid mode: {self.mode}. Must be one of {self.VALID_MODES}")
        if self.mode == "database" and self.db_path is None:
            raise PersistenceValidationError("db_path required for database mode")
        if self.mode == "mock" and self.context is None:
            raise PersistenceValidationError("context required for mock mode")
