# -*- coding: utf-8 -*-
from odoo import _

from .rules import BaseRule, register, SEVERITY_ERROR


@register
class CompanyConsistencyRule(BaseRule):
    code = "SC.VAL.COMP.001"
    title = "采购/结算/付款的公司一致性"
    severity = SEVERITY_ERROR

    def run(self):
        env = self.env
        Payment = env["payment.request"].sudo()
        Settlement = env["sc.settlement.order"].sudo()
        issues = []
        checked = 0

        for pr in Payment.search(self._scope_domain("payment.request")):
            checked += 1
            linked_settlements = pr._linked_settlement_orders()
            bad_settlements = linked_settlements.filtered(
                lambda settle: pr.company_id and settle.company_id and pr.company_id != settle.company_id
            )
            if bad_settlements:
                issues.append(
                    {
                        "model": "payment.request",
                        "res_id": pr.id,
                        "message": _("付款申请与结算单公司不一致"),
                        "refs": {"settlement_ids": bad_settlements.ids},
                    }
                )
            purchase_orders = linked_settlements.mapped("purchase_order_ids")
            if purchase_orders:
                bad = purchase_orders.filtered(
                    lambda po: po.company_id and pr.company_id and po.company_id != pr.company_id
                )
                if bad:
                    issues.append(
                        {
                            "model": "payment.request",
                            "res_id": pr.id,
                            "message": _("付款申请与采购订单公司不一致"),
                            "refs": {"purchase_ids": bad.ids},
                        }
                    )

        for settle in Settlement.search(self._scope_domain("sc.settlement.order")):
            checked += 1
            if settle.purchase_order_ids:
                bad_po = settle.purchase_order_ids.filtered(
                    lambda po: po.company_id and settle.company_id and po.company_id != settle.company_id
                )
                if bad_po:
                    issues.append(
                        {
                            "model": "sc.settlement.order",
                            "res_id": settle.id,
                            "message": _("结算单与采购订单公司不一致"),
                            "refs": {"purchase_ids": bad_po.ids},
                        }
                    )

        return {
            "rule": self.code,
            "title": self.title,
            "severity": self.severity,
            "checked": checked,
            "issues": issues,
        }
