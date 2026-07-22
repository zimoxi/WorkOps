"""
WorkOps Scheduler Service — 调度服务
Sprint035: Backup Scheduler Foundation

管理调度绑定和触发器。不执行真实调度。
"""

import uuid
from datetime import datetime, timezone

from .models import BackupScheduleBinding
from .trigger import SchedulerTrigger
from .errors import SchedulerError


class SchedulerService:
    """
    调度服务。

    管理调度绑定和触发器。不执行真实调度。
    """

    def __init__(self):
        self._bindings: dict[str, BackupScheduleBinding] = {}
        self._triggers: dict[str, SchedulerTrigger] = {}

    def create_binding(
        self,
        job_id: str,
        cron_expression: str,
        enabled: bool = True,
    ) -> BackupScheduleBinding:
        """
        创建调度绑定。

        Args:
            job_id: 任务 ID
            cron_expression: cron 表达式
            enabled: 是否启用

        Returns:
            BackupScheduleBinding
        """
        binding = BackupScheduleBinding(
            binding_id=uuid.uuid4().hex,
            job_id=job_id,
            cron_expression=cron_expression,
            enabled=enabled,
        )
        self._bindings[binding.binding_id] = binding
        return binding

    def get_binding(self, binding_id: str) -> BackupScheduleBinding:
        """获取调度绑定。"""
        binding = self._bindings.get(binding_id)
        if binding is None:
            raise SchedulerError(f"Binding not found: {binding_id}")
        return binding

    def list_bindings(self) -> list[BackupScheduleBinding]:
        """返回所有绑定。"""
        return list(self._bindings.values())

    def evaluate(self) -> list[BackupScheduleBinding]:
        """
        评估所有启用的绑定。

        返回需要触发的绑定列表。
        本 Sprint 只返回所有 enabled 的绑定（不做真实 cron 解析）。
        """
        return [b for b in self._bindings.values() if b.enabled]

    def create_trigger(self, binding_id: str) -> SchedulerTrigger:
        """
        创建触发器。

        Args:
            binding_id: 绑定 ID

        Returns:
            SchedulerTrigger
        """
        binding = self.get_binding(binding_id)
        trigger = SchedulerTrigger.create(binding_id=binding.binding_id)
        self._triggers[trigger.trigger_id] = trigger
        return trigger

    def get_trigger(self, trigger_id: str) -> SchedulerTrigger:
        """获取触发器。"""
        trigger = self._triggers.get(trigger_id)
        if trigger is None:
            raise SchedulerError(f"Trigger not found: {trigger_id}")
        return trigger

    def list_triggers(self) -> list[SchedulerTrigger]:
        """返回所有触发器。"""
        return list(self._triggers.values())
