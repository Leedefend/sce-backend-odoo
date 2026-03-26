# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.project_decision_engine_service import (
    ProjectDecisionEngineService,
)

from .base import BaseProjectBlockBuilder


class ProjectNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.project.next_actions"
    block_type = "action_list"
    title = "下一步动作"
    required_groups = ()

    def build(self, project=None, context=None):
        visibility = self._visibility()
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data={"actions": [], "summary": {}})
        if not project:
            return self._envelope(state="empty", visibility=visibility, data={"actions": [], "summary": {}})

        decision = ProjectDecisionEngineService(self.env).decide(project)
        facts = decision.get("facts") or {}
        lifecycle_state = str(facts.get("lifecycle_state") or "").strip().lower()
        available_action_keys = set(decision.get("available_action_keys") or set())
        priority_scores = decision.get("priority_scores") or {}
        primary_key = str(decision.get("primary_action_key") or "").strip()
        primary_reason = str(decision.get("reason") or "").strip()
        decision_source = str(decision.get("decision_source") or "rule_engine_v1").strip()
        decision_rule = str(decision.get("decision_rule") or "").strip()
        actions = [
            self._next_action(
                project=project,
                key="start_execution",
                label="推进：开始项目执行",
                hint="显式推进项目主线到执行状态，然后进入执行推进场景。",
                action_kind="transition",
                target_scene="project.execution",
                intent="project.connection.transition",
                priority=int(priority_scores.get("start_execution") or 5),
                params={"transition_key": "start_execution", "source": "project.dashboard.next_actions"},
                state="available" if "start_execution" in available_action_keys else "planned",
                reason_code="PROJECT_START_EXECUTION",
                source="product_connection_layer_v1",
                recommended=primary_key == "start_execution",
                reason=primary_reason if primary_key == "start_execution" else "",
                decision_source=decision_source,
                advances_to_stage="execution",
                priority_score=int(priority_scores.get("start_execution") or 0),
            ),
            self._next_action(
                project=project,
                key="project_execution_enter",
                label="下一步：进入执行推进",
                hint="进入项目驾驶舱主链路，从这里继续查看执行、成本、付款和结算。",
                action_kind="guidance",
                target_scene="project.execution",
                intent="project.execution.enter",
                priority=int(priority_scores.get("project_execution_enter") or 10),
                params={"source": "project.dashboard.next_actions"},
                state="available",
                reason_code="PROJECT_EXECUTION_READY",
                source="product_connection_layer_v1",
                recommended=primary_key == "project_execution_enter",
                reason=primary_reason if primary_key == "project_execution_enter" else "",
                decision_source=decision_source,
                advances_to_stage="execution",
                priority_score=int(priority_scores.get("project_execution_enter") or 0),
            ),
            self._next_action(
                project=project,
                key="cost_tracking_enter",
                label="继续：进入成本记录",
                hint="从驾驶舱直接进入成本记录与汇总。",
                action_kind="guidance",
                target_scene="cost.tracking",
                intent="cost.tracking.enter",
                priority=int(priority_scores.get("cost_tracking_enter") or 20),
                params={"source": "project.dashboard.next_actions"},
                state="available" if "cost_tracking_enter" in available_action_keys else "planned",
                reason_code="COST_TRACKING_READY",
                source="product_connection_layer_v1",
                recommended=primary_key == "cost_tracking_enter",
                reason=primary_reason if primary_key == "cost_tracking_enter" else "",
                decision_source=decision_source,
                advances_to_stage="cost",
                priority_score=int(priority_scores.get("cost_tracking_enter") or 0),
            ),
            self._next_action(
                project=project,
                key="payment_enter",
                label="继续：进入付款记录",
                hint="从驾驶舱继续查看或录入付款记录。",
                action_kind="guidance",
                target_scene="payment",
                intent="payment.enter",
                priority=int(priority_scores.get("payment_enter") or 30),
                params={"source": "project.dashboard.next_actions"},
                state="available" if "payment_enter" in available_action_keys else "planned",
                reason_code="PAYMENT_READY",
                source="product_connection_layer_v1",
                recommended=primary_key == "payment_enter",
                reason=primary_reason if primary_key == "payment_enter" else "",
                decision_source=decision_source,
                advances_to_stage="payment",
                priority_score=int(priority_scores.get("payment_enter") or 0),
            ),
            self._next_action(
                project=project,
                key="settlement_enter",
                label="继续：查看结算结果",
                hint="从驾驶舱直接查看项目成本、付款和结算汇总。",
                action_kind="guidance",
                target_scene="settlement",
                intent="settlement.enter",
                priority=int(priority_scores.get("settlement_enter") or 40),
                params={"source": "project.dashboard.next_actions"},
                state="available" if "settlement_enter" in available_action_keys else "planned",
                reason_code="SETTLEMENT_READY",
                source="product_connection_layer_v1",
                recommended=primary_key == "settlement_enter",
                reason=primary_reason if primary_key == "settlement_enter" else "",
                decision_source=decision_source,
                advances_to_stage="settlement",
                priority_score=int(priority_scores.get("settlement_enter") or 0),
            ),
        ]

        next_action_service = self.env["sc.project.next_action.service"]
        try:
            rule_actions = next_action_service.get_next_actions(project, limit=3) or []
        except Exception:
            rule_actions = []
        for index, item in enumerate(rule_actions, start=1):
            if not isinstance(item, dict):
                continue
            actions.append(
                self._next_action(
                    project=project,
                    key=str(item.get("action_ref") or f"project_rule_action_{index}"),
                    label=str(item.get("name") or f"项目动作 {index}"),
                    hint=str(item.get("hint") or ""),
                    action_kind="guidance",
                    target_scene="project.dashboard",
                    intent="ui.contract",
                    priority=100 + index,
                    params={"source": "project.dashboard.next_actions.rule"},
                    state="available",
                    reason_code="PROJECT_RULE_ACTION",
                    source=str(item.get("action_type") or "rule"),
                    recommended=False,
                    reason="",
                    decision_source=decision_source,
                    advances_to_stage="",
                    priority_score=0,
                )
            )

        actions = [row for row in actions if str(row.get("state") or "") == "available"]
        actions = sorted(
            actions,
            key=lambda row: (-int(row.get("priority_score") or 0), int(row.get("priority") or 9999)),
        )
        primary_key = ""
        for row in actions:
            if bool(row.get("recommended")):
                primary_key = str(row.get("key") or "").strip()
                break
        if not primary_key and actions:
            primary_key = str(actions[0].get("key") or "").strip()
        for row in actions:
            is_primary = bool(primary_key) and str(row.get("key") or "").strip() == primary_key
            row["recommended"] = bool(is_primary)
            if is_primary:
                row["reason"] = str(row.get("reason") or "").strip() or "当前项目已经进入主入口，建议先执行这一项以继续推进主线。"
                row["decision_source"] = decision_source
                row["decision_rule"] = decision_rule
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "planned_count": 0,
                    "current_state": lifecycle_state or "dashboard_review",
                    "current_state_label": "已进入项目驾驶舱",
                    "next_step_label": actions[0].get("label") if actions else "进入执行推进",
                    "decision_source": decision_source,
                    "decision_rule": decision_rule,
                },
            },
        )
