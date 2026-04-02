# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Dict, Tuple

from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)

_logger = logging.getLogger(__name__)


class ProjectExecutionTaskTransitionService:
    def __init__(self, env):
        self.env = env

    @staticmethod
    def _task_telemetry(task, *, before_state: str = "", after_state: str = "") -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if task:
            payload["task_id"] = int(getattr(task, "id", 0) or 0)
        if str(before_state or ""):
            payload["task_state_before"] = str(before_state or "")
        if str(after_state or ""):
            payload["task_state_after"] = str(after_state or "")
        return payload

    @staticmethod
    def _log_exception(event: str, **context: Any) -> None:
        _logger.exception("project.execution.advance.%s context=%s", str(event or "unknown"), context)

    def _project_tasks(self, project, *, task_id: int = 0):
        try:
            task_model = self.env["project.task"]
        except Exception:
            self._log_exception(
                "task_model_access_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                task_id=int(task_id or 0),
            )
            return []
        try:
            domain = [("project_id", "=", int(project.id))]
            if int(task_id or 0) > 0:
                domain.append(("id", "=", int(task_id)))
            return task_model.search(domain, order="priority desc, id asc")
        except Exception:
            self._log_exception(
                "task_query_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                task_id=int(task_id or 0),
            )
            return []

    def _actionable_open_task(self, project, *, task_id: int = 0):
        tasks = self._project_tasks(project, task_id=task_id)
        if not tasks:
            return False
        open_tasks = tasks.filtered(lambda rec: ProjectTaskStateSupport.is_open(getattr(rec, "sc_state", "draft")))
        if open_tasks:
            return open_tasks[:1]
        return False

    def _prepare_task_for_execution(self, project, *, task_id: int = 0) -> Tuple[bool, str, Dict[str, Any]]:
        task = self._actionable_open_task(project, task_id=task_id)
        if not task:
            reason_code = "EXECUTION_TASK_TARGET_INVALID" if int(task_id or 0) > 0 else "EXECUTION_TASK_MISSING"
            return False, reason_code, {}
        before_state = ProjectExecutionStateMachine.normalize_task_state(getattr(task, "sc_state", "draft"))
        task_state = before_state
        if task_state not in {"draft", "ready", "in_progress"}:
            return False, "EXECUTION_TASK_START_FAILED", self._task_telemetry(task, before_state=before_state)
        try:
            if task_state == "draft" and hasattr(task, "action_prepare_task"):
                task.action_prepare_task()
                task_state = "ready"
            if task_state == "ready" and hasattr(task, "action_start_task"):
                task.action_start_task()
                task_state = "in_progress"
            ProjectTaskStateSupport.sync_kanban_state(task)
        except Exception:
            self._log_exception(
                "task_prepare_or_start_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                task_id=int(getattr(task, "id", 0) or 0),
                task_state=task_state,
            )
            return False, "EXECUTION_TASK_START_FAILED", self._task_telemetry(task, before_state=before_state)
        after_state = ProjectExecutionStateMachine.normalize_task_state(getattr(task, "sc_state", task_state))
        return (
            after_state == "in_progress",
            "EXECUTION_TRANSITION_READY_TO_IN_PROGRESS",
            self._task_telemetry(task, before_state=before_state, after_state=after_state),
        )

    def _complete_task_for_execution(self, project, *, task_id: int = 0) -> Tuple[bool, str, Dict[str, Any]]:
        tasks = self._project_tasks(project, task_id=task_id)
        if not tasks:
            reason_code = "EXECUTION_TASK_TARGET_INVALID" if int(task_id or 0) > 0 else "EXECUTION_TASK_MISSING"
            return False, reason_code, {}
        task = tasks[:1] if int(task_id or 0) > 0 else tasks.filtered(
            lambda rec: ProjectExecutionStateMachine.normalize_task_state(getattr(rec, "sc_state", "")) == "in_progress"
        )[:1]
        if not task:
            return False, "EXECUTION_TASK_NOT_IN_PROGRESS", {}
        before_state = ProjectExecutionStateMachine.normalize_task_state(getattr(task, "sc_state", ""))
        if before_state != "in_progress":
            return False, "EXECUTION_TASK_NOT_IN_PROGRESS", self._task_telemetry(task, before_state=before_state)
        try:
            if hasattr(task, "action_mark_done"):
                task.action_mark_done()
            ProjectTaskStateSupport.sync_kanban_state(task)
        except Exception:
            self._log_exception(
                "task_complete_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                task_id=int(getattr(task, "id", 0) or 0),
                task_state=before_state,
            )
            return False, "EXECUTION_TASK_COMPLETE_FAILED", self._task_telemetry(task, before_state=before_state)
        after_state = ProjectExecutionStateMachine.normalize_task_state(getattr(task, "sc_state", "done"))
        return (
            True,
            "EXECUTION_TRANSITION_IN_PROGRESS_TO_DONE",
            self._task_telemetry(task, before_state=before_state, after_state=after_state),
        )

    def _recover_task_for_ready(self, project, *, task_id: int = 0) -> Tuple[bool, str, Dict[str, Any]]:
        task = self._actionable_open_task(project, task_id=task_id)
        if not task:
            reason_code = "EXECUTION_TASK_TARGET_INVALID" if int(task_id or 0) > 0 else "EXECUTION_TASK_MISSING"
            return False, reason_code, {}
        before_state = ProjectExecutionStateMachine.normalize_task_state(getattr(task, "sc_state", "draft"))
        try:
            task_state = before_state
            if task_state == "draft" and hasattr(task, "action_prepare_task"):
                task.action_prepare_task()
            ProjectTaskStateSupport.sync_kanban_state(task)
        except Exception:
            self._log_exception(
                "task_recover_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                task_id=int(getattr(task, "id", 0) or 0),
                task_state=before_state,
            )
            return False, "EXECUTION_TASK_RECOVER_FAILED", self._task_telemetry(task, before_state=before_state)
        after_state = ProjectExecutionStateMachine.normalize_task_state(getattr(task, "sc_state", task_state))
        return (
            True,
            "EXECUTION_TRANSITION_BLOCKED_TO_READY",
            self._task_telemetry(task, before_state=before_state, after_state=after_state),
        )

    def apply_real_task_transition(
        self, project, *, from_state: str, to_state: str, task_id: int = 0
    ) -> Tuple[bool, str, Dict[str, Any]]:
        if to_state == "in_progress":
            return self._prepare_task_for_execution(project, task_id=task_id)
        if to_state == "done":
            return self._complete_task_for_execution(project, task_id=task_id)
        if to_state == "ready":
            return self._recover_task_for_ready(project, task_id=task_id)
        return True, ProjectExecutionStateMachine.transition_reason_code(from_state, to_state), {}
