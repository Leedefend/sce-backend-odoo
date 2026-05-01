# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Any

from odoo.exceptions import AccessError

from odoo.addons.smart_construction_core.services.project_execution_consistency_guard import (
    ProjectExecutionConsistencyGuard,
)
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)

_logger = logging.getLogger(__name__)


class ProjectExecutionPostTransitionService:
    def __init__(self, env):
        self.env = env

    @staticmethod
    def _log_exception(event: str, **context: Any) -> None:
        _logger.exception("project.execution.advance.%s context=%s", str(event or "unknown"), context)

    def post_transition_note(self, project, *, from_state: str, to_state: str, reason_code: str, result: str) -> None:
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

    def schedule_followup_activity(self, project, *, to_state: str) -> None:
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
