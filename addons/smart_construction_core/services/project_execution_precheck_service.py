# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Tuple

from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)


class ProjectExecutionPrecheckService:
    STAGE_TRANSITION = "transition"
    STAGE_SCOPE = "scope"
    STAGE_ALIGNMENT = "alignment"

    def __init__(self, consistency_guard):
        self.consistency_guard = consistency_guard

    def evaluate(self, project, *, from_state: str, to_state: str) -> Tuple[bool, str, str]:
        if not ProjectExecutionStateMachine.can_transition(from_state, to_state):
            return False, self.STAGE_TRANSITION, ProjectExecutionStateMachine.transition_reason_code(from_state, to_state)

        scope_ok, scope_reason_code, _summary = self.consistency_guard.validate_scope(
            project, from_state=from_state, to_state=to_state
        )
        if not scope_ok:
            return False, self.STAGE_SCOPE, str(scope_reason_code or "")

        alignment_ok, alignment_reason_code, _summary = self.consistency_guard.validate_state_alignment(project)
        if not alignment_ok and from_state != "ready":
            return False, self.STAGE_ALIGNMENT, str(alignment_reason_code or "")

        return True, "", ""
