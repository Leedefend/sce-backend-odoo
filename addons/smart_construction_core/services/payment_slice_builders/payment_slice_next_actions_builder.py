# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo.addons.smart_construction_core.services.payment_slice_native_adapter import PaymentSliceNativeAdapter
from odoo.addons.smart_construction_core.services.project_dashboard_builders.base import BaseProjectBlockBuilder


class PaymentSliceNextActionsBuilder(BaseProjectBlockBuilder):
    block_key = "block.payment.slice_next_actions"
    block_type = "action_list"
    title = "付款下一步"
    required_groups = ()

    def build(self, project=None, context=None):
        del context
        visibility = self._visibility()
        empty_data = {"actions": [], "summary": {}}
        if not visibility.get("allowed"):
            return self._envelope(state="forbidden", visibility=visibility, data=empty_data)
        if not project:
            return self._envelope(state="empty", visibility=visibility, data=empty_data)

        summary = PaymentSliceNativeAdapter(self.env).summary(project)
        actions = [
            self._next_action(
                project=project,
                key="refresh_payment_list",
                label="继续：刷新付款记录",
                hint="已接入付款录入、付款记录和付款汇总。若刚录入完成，可刷新区块核对结果。",
                action_kind="guidance",
                target_scene="payment",
                intent="payment.block.fetch",
                priority=10,
                params={"block_key": "payment_list"},
                state="available",
                reason_code="PAYMENT_SLICE_REFRESH_READY",
                source="fr4_prepared",
            )
        ]
        actions.append(
            self._next_action(
                project=project,
                key="settlement_enter",
                label="下一步：查看结算结果",
                hint="基于当前项目成本与付款事实，进入 FR-5 结算切片查看只读汇总。",
                action_kind="guidance",
                target_scene="settlement",
                intent="settlement.enter",
                priority=20,
                params={"source": "payment.slice.next_actions"},
                state="available",
                reason_code="SETTLEMENT_SLICE_READY",
                source="fr5_prepared",
            )
        )
        return self._envelope(
            state="ready",
            visibility=visibility,
            data={
                "actions": actions,
                "summary": {
                    "count": len(actions),
                    "available_count": len(actions),
                    "planned_count": 0,
                    "current_state": "payment_slice_prepared",
                    "current_state_label": "付款切片 Prepared",
                    "next_step_label": "录入付款或查看结算结果",
                    "record_count": int(summary.get("request_count") or 0),
                },
            },
        )
