# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class SettlementSliceNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.settlement.slice_next_actions"
    block_type = "action_list"
    title = "结算下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        actions = [
            self._next_action(
                project=project,
                key="view_summary",
                label="继续：查看结算摘要",
                hint="刷新当前结算结果区块，确认成本、付款与差额。",
                action_kind="guidance",
                target_scene="settlement",
                intent="settlement.block.fetch",
                priority=10,
                params={"block_key": "settlement_summary"},
                state="available",
                reason_code="SETTLEMENT_SUMMARY_READY",
                source="product_connection_layer_v1",
            ),
            self._next_action(
                project=project,
                key="confirm_settlement",
                label="推进：确认进入结算",
                hint="当项目已经具备结算条件时，显式推进项目生命周期到结算收口状态。",
                action_kind="transition",
                target_scene="settlement",
                intent="project.connection.transition",
                priority=20,
                params={"transition_key": "confirm_settlement", "source": "settlement.next_actions"},
                state="available" if lifecycle_state in {"in_progress", "closing", "warranty"} else "planned",
                reason_code="SETTLEMENT_CONFIRM_READY",
                source="product_connection_layer_v1",
            ),
            self._next_action(
                project=project,
                key="complete_project",
                label="推进：完成项目",
                hint="在结算确认后显式完成项目，形成闭环。",
                action_kind="transition",
                target_scene="settlement",
                intent="project.connection.transition",
                priority=30,
                params={"transition_key": "complete_project", "source": "settlement.next_actions"},
                state="available" if lifecycle_state in {"warranty", "closing", "done"} else "planned",
                reason_code="PROJECT_COMPLETE_READY",
                source="product_connection_layer_v1",
            ),
        ]
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "available_count": len([row for row in actions if str(row.get("state") or "") == "available"]),
                    "planned_count": len([row for row in actions if str(row.get("state") or "") == "planned"]),
                    "current_state": lifecycle_state or "settlement_review",
                    "current_state_label": "结算收口",
                    "next_step_label": "查看结算摘要或推进项目完成",
                },
            },
        )
