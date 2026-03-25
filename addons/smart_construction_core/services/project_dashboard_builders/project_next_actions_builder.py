# -*- coding: utf-8 -*-
from __future__ import annotations

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

        lifecycle_state = str(getattr(project, "lifecycle_state", "") or "").strip().lower()
        cost_count = self._safe_count("account.move", self._project_domain("account.move", project))
        payment_count = self._safe_count("payment.request", self._project_domain("payment.request", project))
        recommend_cost = lifecycle_state in {"in_progress", "closing", "warranty", "done"} and cost_count <= 0
        recommend_payment = lifecycle_state in {"in_progress", "closing", "warranty", "done"} and cost_count > 0 and payment_count <= 0
        recommend_settlement = lifecycle_state in {"closing", "warranty", "done"} and cost_count > 0 and payment_count > 0
        actions = [
            self._next_action(
                project=project,
                key="start_execution",
                label="推进：开始项目执行",
                hint="显式推进项目主线到执行状态，然后进入执行推进场景。",
                action_kind="transition",
                target_scene="project.execution",
                intent="project.connection.transition",
                priority=5,
                params={"transition_key": "start_execution", "source": "project.dashboard.next_actions"},
                state="available" if lifecycle_state == "draft" else "planned",
                reason_code="PROJECT_START_EXECUTION",
                source="product_connection_layer_v1",
                recommended=lifecycle_state == "draft",
                reason="项目已完成立项，下一步应显式进入执行阶段。" if lifecycle_state == "draft" else "",
            ),
            self._next_action(
                project=project,
                key="project_execution_enter",
                label="下一步：进入执行推进",
                hint="进入项目驾驶舱主链路，从这里继续查看执行、成本、付款和结算。",
                action_kind="guidance",
                target_scene="project.execution",
                intent="project.execution.enter",
                priority=10,
                params={"source": "project.dashboard.next_actions"},
                state="available",
                reason_code="PROJECT_EXECUTION_READY",
                source="product_connection_layer_v1",
                recommended=lifecycle_state == "draft",
                reason="当前项目已就绪，建议先进入执行推进确认任务状态。" if lifecycle_state == "draft" else "",
            ),
            self._next_action(
                project=project,
                key="cost_tracking_enter",
                label="继续：进入成本记录",
                hint="从驾驶舱直接进入成本记录与汇总。",
                action_kind="guidance",
                target_scene="cost.tracking",
                intent="cost.tracking.enter",
                priority=20,
                params={"source": "project.dashboard.next_actions"},
                state="available" if lifecycle_state in {"in_progress", "closing", "warranty", "done"} else "planned",
                reason_code="COST_TRACKING_READY",
                source="product_connection_layer_v1",
                recommended=recommend_cost,
                reason="当前项目已进入执行阶段，建议优先录入成本，形成经营事实基线。" if recommend_cost else "",
            ),
            self._next_action(
                project=project,
                key="payment_enter",
                label="继续：进入付款记录",
                hint="从驾驶舱继续查看或录入付款记录。",
                action_kind="guidance",
                target_scene="payment",
                intent="payment.enter",
                priority=30,
                params={"source": "project.dashboard.next_actions"},
                state="available" if lifecycle_state in {"in_progress", "closing", "warranty", "done"} else "planned",
                reason_code="PAYMENT_READY",
                source="product_connection_layer_v1",
                recommended=recommend_payment,
                reason="当前项目已有成本记录，建议继续录入付款，完成资金侧闭环。" if recommend_payment else "",
            ),
            self._next_action(
                project=project,
                key="settlement_enter",
                label="继续：查看结算结果",
                hint="从驾驶舱直接查看项目成本、付款和结算汇总。",
                action_kind="guidance",
                target_scene="settlement",
                intent="settlement.enter",
                priority=40,
                params={"source": "project.dashboard.next_actions"},
                state="available" if lifecycle_state in {"closing", "warranty", "done"} else "planned",
                reason_code="SETTLEMENT_READY",
                source="product_connection_layer_v1",
                recommended=recommend_settlement,
                reason="当前项目已具备成本与付款事实，建议进入结算结果检查是否满足收口条件。" if recommend_settlement else "",
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
                )
            )

        actions = sorted(actions, key=lambda row: int(row.get("priority") or 9999))
        if not any(bool(row.get("recommended")) for row in actions):
            for row in actions:
                if str(row.get("state") or "") != "available":
                    continue
                row["recommended"] = True
                row["reason"] = str(row.get("reason") or "").strip() or "当前项目已经进入主入口，建议先执行这一项以继续推进主线。"
                break
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "planned_count": len([row for row in actions if str(row.get("state") or "") == "planned"]),
                    "current_state": lifecycle_state or "dashboard_review",
                    "current_state_label": "已进入项目驾驶舱",
                    "next_step_label": "进入执行推进",
                },
            },
        )
