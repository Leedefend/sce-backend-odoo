# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder
from odoo.addons.smart_construction_core.services.project_execution_state_machine import (
    ProjectExecutionStateMachine,
)


class ProjectExecutionNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.execution_next_actions"
    block_type = "action_list"
    title = "执行下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        current_state = ProjectExecutionStateMachine.normalize_state(getattr(project, "sc_execution_state", "ready"))
        action = ProjectExecutionStateMachine.action_payload(int(project.id), current_state)
        actions = [action]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "ready_count": len([row for row in actions if str(row.get("state") or "") == "ready"]),
                    "blocked_count": len([row for row in actions if str(row.get("state") or "") == "blocked"]),
                    "current_state": current_state,
                    "current_state_label": ProjectExecutionStateMachine.STATE_LABEL.get(current_state, current_state),
                    "allowed_targets": list(ProjectExecutionStateMachine.allowed_targets(current_state)),
                    "next_step_label": str(action.get("label") or ""),
                },
            },
        )
