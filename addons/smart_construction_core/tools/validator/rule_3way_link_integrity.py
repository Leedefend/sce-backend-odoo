# -*- coding: utf-8 -*-
from odoo import _

from .rules import DataRule, register


@register
class ThreeWayLinkIntegrityRule(DataRule):
    name = "three_way_link_integrity"
    level = "error"
    description = "三单匹配链路的关键关联是否缺失"

    def run(self):
        env = self.env
        Payment = env["payment.request"].sudo()
        Settlement = env["sc.settlement.order"].sudo()
        issues = []
        checked = 0
        pr_states_need_settle = ("approve", "approved", "done")
        settle_states_need_po = ("approve", "done")

        for pr in Payment.search([]):
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

        for settle in Settlement.search([]):
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
            "rule": self.name,
            "level": self.level,
            "checked": checked,
            "issues": issues,
        }
