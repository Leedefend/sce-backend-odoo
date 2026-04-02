# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Tuple

from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)

_logger = logging.getLogger(__name__)


class ExecutionAdvanceAtomicRollback(Exception):
    """Signal a blocked reason that must rollback the atomic transition section."""

    def __init__(self, reason_code: str, task_telemetry: Dict[str, Any] | None = None):
        self.reason_code = str(reason_code or "EXECUTION_TRANSITION_FAILED")
        self.task_telemetry = dict(task_telemetry or {})
        super().__init__(self.reason_code)


class ProjectExecutionTransitionService:
    @staticmethod
    def apply_transition_atomically(
        *,
        env,
        project,
        from_state: str,
        to_state: str,
        consistency_guard,
        transition_runner: Callable[..., Tuple[bool, str, Dict[str, Any]]],
        trace_id: str = "",
    ) -> Tuple[str, Dict[str, Any]]:
        with env.cr.savepoint():
            task_success, task_reason_code, task_telemetry = transition_runner(
                project=project, from_state=from_state, to_state=to_state
            )
            if not task_success:
                raise ExecutionAdvanceAtomicRollback(task_reason_code, task_telemetry)

            try:
                project.sudo().write({"sc_execution_state": to_state})
            except Exception:
                _logger.exception(
                    "project.execution.advance.project_state_write_failed "
                    "project_id=%s from_state=%s to_state=%s trace_id=%s",
                    int(getattr(project, "id", 0) or 0),
                    str(from_state or ""),
                    str(to_state or ""),
                    str(trace_id or ""),
                )
                raise ExecutionAdvanceAtomicRollback("EXECUTION_TRANSITION_WRITE_FAILED", task_telemetry)

            alignment_ok, alignment_reason_code, _summary = consistency_guard.validate_state_alignment(project)
            if not alignment_ok:
                raise ExecutionAdvanceAtomicRollback(alignment_reason_code, task_telemetry)

        return task_reason_code or ProjectExecutionStateMachine.transition_reason_code(from_state, to_state), task_telemetry
