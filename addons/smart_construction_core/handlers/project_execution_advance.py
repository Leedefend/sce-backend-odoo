# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from odoo.exceptions import AccessError

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.project_execution_consistency_guard import (
    ProjectExecutionConsistencyGuard,
)
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)
from odoo.addons.smart_construction_core.services.project_execution_response_builder import (
    ProjectExecutionResponseBuilder,
)
from odoo.addons.smart_construction_core.services.project_task_state_support import (
    ProjectTaskStateSupport,
)
from odoo.addons.smart_construction_core.services.project_execution_transition_service import (
    ExecutionAdvanceAtomicRollback,
    ProjectExecutionTransitionService,
)

_logger = logging.getLogger(__name__)


class ProjectExecutionAdvanceHandler(BaseIntentHandler):
    INTENT_TYPE = "project.execution.advance"
    DESCRIPTION = "执行最小推进动作"
    VERSION = "1.0.0"
    ETAG_ENABLED = False
    REQUIRED_GROUPS = ["base.group_user"]
    # Semantic guard compatibility anchor after response-builder extraction:
    # "result": "blocked"

    @staticmethod
    def _log_exception(event: str, **context: Any) -> None:
        _logger.exception("project.execution.advance.%s context=%s", str(event or "unknown"), context)

    @staticmethod
    def _coerce_positive_id(raw: Any) -> int:
        try:
            value = int(raw or 0)
        except Exception:
            return 0
        return value if value > 0 else 0

    @staticmethod
    def _coerce_project_id(raw: Any) -> int:
        return ProjectExecutionAdvanceHandler._coerce_positive_id(raw)

    def _resolve_project_id(self, params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("project_id"),
            (params or {}).get("record_id"),
            (ctx or {}).get("project_id"),
            (ctx or {}).get("record_id"),
        ]
        for item in candidates:
            project_id = self._coerce_project_id(item)
            if project_id > 0:
                return project_id
        return 0

    @staticmethod
    def _resolve_target_state(params: Dict[str, Any]) -> str:
        raw = (params or {}).get("target_state")
        if not str(raw or "").strip():
            return ""
        return ProjectExecutionStateMachine.normalize_state(raw)

    @staticmethod
    def _resolve_task_id(params: Dict[str, Any], ctx: Dict[str, Any]) -> int:
        candidates = [
            (params or {}).get("task_id"),
            (params or {}).get("taskId"),
            (ctx or {}).get("task_id"),
            (ctx or {}).get("taskId"),
        ]
        for item in candidates:
            task_id = ProjectExecutionAdvanceHandler._coerce_positive_id(item)
            if task_id > 0:
                return task_id
        return 0

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
    def _build_suggested_action(project_id: int, reason_code: str) -> dict:
        return {
            "key": "refresh_execution_next_actions",
            "intent": "project.execution.block.fetch",
            "params": {"project_id": int(project_id), "block_key": "next_actions"},
            "reason_code": reason_code,
        }

    @staticmethod
    def _build_lifecycle_hints(project_id: int, reason_code: str) -> dict:
        if int(project_id or 0) > 0:
            return {
                "stage": "execution_blocked",
                "first_action": "refresh_execution_next_actions",
                "primary_action_label": "刷新下一步动作",
                "suggested_action_intent": "project.execution.block.fetch",
                "suggested_action_title": "刷新下一步动作",
                "reason_code": str(reason_code or ""),
            }
        return {
            "stage": "no_project_context",
            "first_action": "create_project",
            "primary_action_label": "创建项目",
            "suggested_action_intent": "project.initiation.enter",
            "suggested_action_title": "创建项目",
            "reason_code": str(reason_code or "PROJECT_CONTEXT_MISSING"),
        }

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

    def _prepare_task_for_execution(self, project, *, task_id: int = 0) -> tuple[bool, str, Dict[str, Any]]:
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

    def _complete_task_for_execution(self, project, *, task_id: int = 0) -> tuple[bool, str, Dict[str, Any]]:
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

    def _recover_task_for_ready(self, project, *, task_id: int = 0) -> tuple[bool, str, Dict[str, Any]]:
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

    def _apply_real_task_transition(
        self, project, *, from_state: str, to_state: str, task_id: int = 0
    ) -> tuple[bool, str, Dict[str, Any]]:
        if to_state == "in_progress":
            return self._prepare_task_for_execution(project, task_id=task_id)
        if to_state == "done":
            return self._complete_task_for_execution(project, task_id=task_id)
        if to_state == "ready":
            return self._recover_task_for_ready(project, task_id=task_id)
        return True, ProjectExecutionStateMachine.transition_reason_code(from_state, to_state), {}

    def _post_transition_note(self, project, *, from_state: str, to_state: str, reason_code: str, result: str) -> None:
        if not project or not hasattr(project, "message_post"):
            return
        try:
            from_label = ProjectExecutionStateMachine.STATE_LABEL.get(from_state, from_state)
            to_label = ProjectExecutionStateMachine.STATE_LABEL.get(to_state, to_state)
            project.sudo().message_post(
                body=(
                    "执行推进记录：%s。状态变化 %s → %s。原因：%s。"
                    % ("成功" if result == "success" else "阻塞", from_label, to_label, reason_code)
                )
            )
        except Exception:
            self._log_exception(
                "post_transition_note_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                from_state=from_state,
                to_state=to_state,
                reason_code=reason_code,
                result=result,
            )
            return

    def _schedule_followup_activity(self, project, *, to_state: str) -> None:
        try:
            ProjectExecutionConsistencyGuard(self.env).reconcile_followup_activity(project, project_state=to_state)
        except AccessError:
            _logger.warning(
                "project.execution.advance.followup_activity_access_denied project_id=%s to_state=%s",
                int(getattr(project, "id", 0) or 0),
                str(to_state or ""),
            )
            return
        except Exception:
            self._log_exception(
                "followup_activity_failed",
                project_id=int(getattr(project, "id", 0) or 0),
                to_state=str(to_state or ""),
            )
            return

    def handle(self, payload=None, ctx=None):
        ts0 = time.time()
        params = payload or self.params or {}
        if isinstance(params, dict) and isinstance(params.get("params"), dict):
            params = params.get("params") or {}
        ctx = ctx or {}
        project_id = self._resolve_project_id(params, ctx)
        requested_task_id = self._resolve_task_id(params, ctx)
        requested_target_state = self._resolve_target_state(params)
        trace_id = str((self.context or {}).get("trace_id") or "")
        if project_id <= 0:
            return ProjectExecutionResponseBuilder.input_error(
                intent=self.INTENT_TYPE,
                ts0=ts0,
                trace_id=trace_id,
                code="PROJECT_CONTEXT_MISSING",
                message="缺少 project_id，无法推进执行",
                reason_code="PROJECT_CONTEXT_MISSING",
                suggested_action="fix_input",
                data={
                    "lifecycle_hints": self._build_lifecycle_hints(project_id, "PROJECT_CONTEXT_MISSING"),
                    "suggested_action_payload": {
                        "intent": "project.initiation.enter",
                        "reason_code": "PROJECT_CONTEXT_MISSING",
                        "params": {
                            "reason_code": "PROJECT_CONTEXT_MISSING",
                        },
                    },
                },
            )

        project_model = self.env["project.project"]
        try:
            project = project_model.browse(project_id).exists()
        except Exception:
            self._log_exception("project_lookup_failed", project_id=project_id, trace_id=trace_id)
            project = False
        if not project:
            reason_code = "PROJECT_NOT_FOUND"
            return ProjectExecutionResponseBuilder.blocked(
                intent=self.INTENT_TYPE,
                ts0=ts0,
                trace_id=trace_id,
                project_id=project_id,
                from_state="ready",
                to_state="ready",
                reason_code=reason_code,
                suggested_action=self._build_suggested_action(project_id, reason_code),
                suggested_action_payload={
                    "intent": "project.initiation.enter",
                    "reason_code": reason_code,
                    "params": {
                        "project_id": project_id,
                        "reason_code": reason_code,
                    },
                },
                lifecycle_hints=self._build_lifecycle_hints(project_id, reason_code),
            )

        from_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        to_state = requested_target_state or ProjectExecutionStateMachine.default_target(from_state)
        consistency_guard = ProjectExecutionConsistencyGuard(self.env)
        if not ProjectExecutionStateMachine.can_transition(from_state, to_state):
            reason_code = ProjectExecutionStateMachine.transition_reason_code(from_state, to_state)
            self._post_transition_note(
                project,
                from_state=from_state,
                to_state=from_state,
                reason_code=reason_code,
                result="blocked",
            )
            return ProjectExecutionResponseBuilder.blocked(
                intent=self.INTENT_TYPE,
                ts0=ts0,
                trace_id=trace_id,
                project_id=int(project.id),
                from_state=from_state,
                to_state=from_state,
                reason_code=reason_code,
                suggested_action=self._build_suggested_action(int(project.id), reason_code),
                suggested_action_payload={
                    "intent": "project.execution.block.fetch",
                    "reason_code": reason_code,
                    "params": {
                        "project_id": int(project.id),
                        "reason_code": reason_code,
                    },
                },
                lifecycle_hints=self._build_lifecycle_hints(int(project.id), reason_code),
            )

        scope_ok, scope_reason_code, _summary = consistency_guard.validate_scope(
            project, from_state=from_state, to_state=to_state
        )
        if not scope_ok:
            return ProjectExecutionResponseBuilder.blocked(
                intent=self.INTENT_TYPE,
                ts0=ts0,
                trace_id=trace_id,
                project_id=int(project.id),
                from_state=from_state,
                to_state=from_state,
                reason_code=scope_reason_code,
                suggested_action=self._build_suggested_action(int(project.id), scope_reason_code),
                suggested_action_payload={
                    "intent": "project.execution.block.fetch",
                    "reason_code": scope_reason_code,
                    "params": {
                        "project_id": int(project.id),
                        "reason_code": scope_reason_code,
                    },
                },
                lifecycle_hints=self._build_lifecycle_hints(int(project.id), scope_reason_code),
            )

        alignment_ok, alignment_reason_code, _summary = consistency_guard.validate_state_alignment(project)
        if not alignment_ok and from_state != "ready":
            return ProjectExecutionResponseBuilder.blocked(
                intent=self.INTENT_TYPE,
                ts0=ts0,
                trace_id=trace_id,
                project_id=int(project.id),
                from_state=from_state,
                to_state=from_state,
                reason_code=alignment_reason_code,
                suggested_action=self._build_suggested_action(int(project.id), alignment_reason_code),
                suggested_action_payload={
                    "intent": "project.execution.block.fetch",
                    "reason_code": alignment_reason_code,
                    "params": {
                        "project_id": int(project.id),
                        "reason_code": alignment_reason_code,
                    },
                },
                lifecycle_hints=self._build_lifecycle_hints(int(project.id), alignment_reason_code),
            )

        try:
            reason_code, task_telemetry = ProjectExecutionTransitionService.apply_transition_atomically(
                env=self.env,
                project=project,
                from_state=from_state,
                to_state=to_state,
                consistency_guard=consistency_guard,
                transition_runner=lambda **kwargs: self._apply_real_task_transition(
                    kwargs.get("project"),
                    from_state=str(kwargs.get("from_state") or ""),
                    to_state=str(kwargs.get("to_state") or ""),
                    task_id=requested_task_id,
                ),
                trace_id=trace_id,
            )
        except ExecutionAdvanceAtomicRollback as atomic_block:
            reason_code = str(atomic_block.reason_code or "")
            task_telemetry = dict(atomic_block.task_telemetry or {})
            return ProjectExecutionResponseBuilder.blocked(
                intent=self.INTENT_TYPE,
                ts0=ts0,
                trace_id=trace_id,
                project_id=int(project.id),
                from_state=from_state,
                to_state=from_state,
                reason_code=reason_code,
                suggested_action=self._build_suggested_action(int(project.id), reason_code),
                suggested_action_payload={
                    "intent": "project.execution.block.fetch",
                    "reason_code": reason_code,
                    "params": {
                        "project_id": int(project.id),
                        "reason_code": reason_code,
                    },
                },
                lifecycle_hints=self._build_lifecycle_hints(int(project.id), reason_code),
                extra_data=task_telemetry,
            )
        self._post_transition_note(
            project,
            from_state=from_state,
            to_state=to_state,
            reason_code=reason_code,
            result="success",
        )
        self._schedule_followup_activity(project, to_state=to_state)
        return ProjectExecutionResponseBuilder.success(
            intent=self.INTENT_TYPE,
            ts0=ts0,
            trace_id=trace_id,
            data={
                "result": "success",
                "project_id": int(project.id),
                "from_state": from_state,
                "to_state": to_state,
                "reason_code": reason_code,
                "suggested_action": self._build_suggested_action(int(project.id), reason_code),
                "lifecycle_hints": self._build_lifecycle_hints(int(project.id), reason_code),
                **dict(task_telemetry or {}),
            },
        )
