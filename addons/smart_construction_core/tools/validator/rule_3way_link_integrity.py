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
        scope = self.scope or {}
        scoped_model = str(scope.get("res_model") or "")
        scoped_res_ids = scope.get("res_ids") or []
        issues = []
        checked = 0
        pr_states_need_settle = ("approve", "approved", "done")
        settle_states_need_po = ("approve", "done")
        targeted_payment_scope = scoped_model == "payment.request" and bool(scoped_res_ids)
        targeted_settlement_scope = scoped_model == "sc.settlement.order" and bool(scoped_res_ids)

        payment_domain = self._scope_domain("payment.request")
        if targeted_settlement_scope:
            payment_domain = [("settlement_id", "in", scoped_res_ids)]

        for pr in Payment.search(payment_domain):
            checked += 1
            # 仅对支出付款单执行三单匹配校验
            if pr.type != "pay" or pr.state not in pr_states_need_settle:
                continue
            if not pr.settlement_id:
                continue
            if pr.settlement_id.state in settle_states_need_po and not pr.settlement_id.purchase_order_ids:
                issues.append(
                    {
                        "model": "payment.request",
                        "res_id": pr.id,
                        "message": _("结算单未关联采购订单"),
                        "refs": {"settlement_id": pr.settlement_id.id, "name": pr.settlement_id.name},
                    }
            )

        if not targeted_payment_scope:
            for settle in Settlement.search(self._scope_domain("sc.settlement.order")):
                checked += 1
                if settle.settlement_type != "out" or settle.state not in settle_states_need_po:
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
