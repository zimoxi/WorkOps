"""
WorkOps Restore Workflow Errors — 恢复工作流错误
Sprint042: Restore Workflow Foundation v1
"""


class RestoreWorkflowV1Error(Exception):
    """恢复工作流错误基类"""
    pass


class InvalidRestoreRequestError(RestoreWorkflowV1Error):
    """无效恢复请求"""
    pass


class RestoreConflictError(RestoreWorkflowV1Error):
    """恢复冲突"""
    def __init__(self, restore_id: str):
        super().__init__(f"Restore already exists: {restore_id}")


class RestoreNotFoundError(RestoreWorkflowV1Error):
    """恢复未找到"""
    def __init__(self, restore_id: str):
        super().__init__(f"Restore not found: {restore_id}")
