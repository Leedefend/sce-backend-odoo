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

        for pr in Payment.search([]):
            checked += 1
            settle = pr.settlement_id
            if settle and pr.company_id and settle.company_id and pr.company_id != settle.company_id:
                issues.append(
                    {
                        "model": "payment.request",
                        "res_id": pr.id,
                        "message": _("付款申请与结算单公司不一致"),
                        "refs": {"settlement_id": settle.id},
                    }
                )
            if settle and settle.purchase_order_ids:
                bad = settle.purchase_order_ids.filtered(
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

        for settle in Settlement.search([]):
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
