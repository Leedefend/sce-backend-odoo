# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import time
from typing import Any, Dict

from odoo.addons.smart_core.core.base_handler import BaseIntentHandler
from odoo.addons.smart_construction_core.services.project_execution_consistency_guard import (
    ProjectExecutionConsistencyGuard,
)
from odoo.addons.smart_construction_core.services.project_execution_post_transition_service import (
    ProjectExecutionPostTransitionService,
)
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)
from odoo.addons.smart_construction_core.services.project_execution_response_builder import (
    ProjectExecutionResponseBuilder,
)
from odoo.addons.smart_construction_core.services.project_execution_precheck_service import (
    ProjectExecutionPrecheckService,
)
from odoo.addons.smart_construction_core.services.project_execution_task_transition_service import (
    ProjectExecutionTaskTransitionService,
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

    def _task_transition_service(self) -> ProjectExecutionTaskTransitionService:
        return ProjectExecutionTaskTransitionService(self.env)

    def _precheck_service(self, consistency_guard) -> ProjectExecutionPrecheckService:
        return ProjectExecutionPrecheckService(consistency_guard)

    def _post_transition_service(self) -> ProjectExecutionPostTransitionService:
        return ProjectExecutionPostTransitionService(self.env)

    def _blocked_response(
        self,
        *,
        ts0: float,
        trace_id: str,
        project_id: int,
        from_state: str,
        reason_code: str,
        extra_data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        return ProjectExecutionResponseBuilder.blocked(
            intent=self.INTENT_TYPE,
            ts0=ts0,
            trace_id=trace_id,
            project_id=project_id,
            from_state=from_state,
            to_state=from_state,
            reason_code=reason_code,
            suggested_action=self._build_suggested_action(project_id, reason_code),
            suggested_action_payload={
                "intent": "project.execution.block.fetch",
                "reason_code": reason_code,
                "params": {
                    "project_id": project_id,
                    "reason_code": reason_code,
                },
            },
            lifecycle_hints=self._build_lifecycle_hints(project_id, reason_code),
            extra_data=extra_data,
        )

    def _apply_real_task_transition(
        self, project, *, from_state: str, to_state: str, task_id: int = 0
    ) -> tuple[bool, str, Dict[str, Any]]:
        return self._task_transition_service().apply_real_task_transition(
            project,
            from_state=from_state,
            to_state=to_state,
            task_id=task_id,
        )

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
        precheck_ok, precheck_stage, precheck_reason_code = self._precheck_service(consistency_guard).evaluate(
            project, from_state=from_state, to_state=to_state
        )
        if not precheck_ok:
            reason_code = str(precheck_reason_code or "EXECUTION_TRANSITION_BLOCKED")
            if precheck_stage == ProjectExecutionPrecheckService.STAGE_TRANSITION:
                self._post_transition_service().post_transition_note(
                    project,
                    from_state=from_state,
                    to_state=from_state,
                    reason_code=reason_code,
                    result="blocked",
                )
            return self._blocked_response(
                ts0=ts0,
                trace_id=trace_id,
                project_id=int(project.id),
                from_state=from_state,
                reason_code=reason_code,
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
            return self._blocked_response(
                ts0=ts0,
                trace_id=trace_id,
                project_id=int(project.id),
                from_state=from_state,
                reason_code=reason_code,
                extra_data=task_telemetry,
            )

        self._post_transition_service().post_transition_note(
            project,
            from_state=from_state,
            to_state=to_state,
            reason_code=reason_code,
            result="success",
        )
        self._post_transition_service().schedule_followup_activity(project, to_state=to_state)
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
