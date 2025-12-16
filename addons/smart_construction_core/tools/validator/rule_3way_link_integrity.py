# -*- coding: utf-8 -*-
from odoo import _

from .rules import BaseRule, register, SEVERITY_ERROR


@register
class ThreeWayLinkIntegrityRule(BaseRule):
    code = "SC.VAL.3WAY.001"
    title = "三单匹配链路的关键关联是否缺失"
    severity = SEVERITY_ERROR

    def run(self):
        env = self.env
        Payment = env["payment.request"].sudo()
        Settlement = env["sc.settlement.order"].sudo()
        issues = []
        checked = 0
        pr_states_need_settle = ("approve", "approved", "done")
        settle_states_need_po = ("approve", "done")

        def _suggest_settlements(rec):
            """给出同项目+同供应商的候选结算单（最近3条批准态优先）。"""
            domain = [
                ("project_id", "=", rec.project_id.id),
                ("partner_id", "=", rec.partner_id.id),
                ("state", "in", settle_states_need_po),
            ]
            candidates = Settlement.search(
                self._scope_domain("sc.settlement.order") + domain,
                limit=3,
                order="create_date desc, id desc",
            )
            return [
                {
                    "res_model": "sc.settlement.order",
                    "res_id": s.id,
                    "display_name": s.display_name or s.name,
                    "project_id": s.project_id.id,
                    "partner_id": s.partner_id.id,
                    "reason": _("同项目同供应商的最近结算单"),
                    "score": 0.8,
                    "action": {"type": "open_form", "res_model": "sc.settlement.order", "res_id": s.id},
                }
                for s in candidates
            ]

        for pr in Payment.search(self._scope_domain("payment.request")):
            checked += 1
            if pr.state not in pr_states_need_settle:
                continue
            if not pr.settlement_id:
                issues.append(
                    {
                        "model": "payment.request",
                        "res_id": pr.id,
                        "message": _("付款申请未关联结算单"),
                        "refs": {"name": pr.name},
                        "suggestions": _suggest_settlements(pr),
                    }
                )
            elif pr.settlement_id.state in settle_states_need_po and not pr.settlement_id.purchase_order_ids:
                issues.append(
                    {
                        "model": "payment.request",
                        "res_id": pr.id,
                        "message": _("结算单未关联采购订单"),
                        "refs": {"settlement_id": pr.settlement_id.id, "name": pr.settlement_id.name},
                    }
                )

        for settle in Settlement.search(self._scope_domain("sc.settlement.order")):
            checked += 1
            if settle.state not in settle_states_need_po:
                continue
            if settle.purchase_order_ids:
                continue
            issues.append(
                {
                    "model": "sc.settlement.order",
                    "res_id": settle.id,
                    "message": _("结算单未关联采购订单"),
                    "refs": {"name": settle.name},
                }
            )

        return {
            "rule": self.code,
            "title": self.title,
            "severity": self.severity,
            "checked": checked,
            "issues": issues,
        }
