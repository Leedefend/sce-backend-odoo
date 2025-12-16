# -*- coding: utf-8 -*-
from odoo import _
from odoo.tools.float_utils import float_compare

from .rules import BaseRule, register, SEVERITY_ERROR
from ...models.support import operating_metrics as opm


@register
class PaymentNotOverpayRule(BaseRule):
    code = "SC.VAL.PAY.001"
    title = _("付款不得超过结算可付余额")
    severity = SEVERITY_ERROR

    def run(self):
        env = self.env
        Payment = env["payment.request"].sudo()

        domain = [
            ("type", "=", "pay"),
            ("settlement_id", "!=", False),
            ("amount", ">", 0),
            ("state", "in", ("draft", "submit", "approve", "approved")),
        ]
        domain += self._scope_domain("payment.request")

        issues = []
        checked = 0

        paid_states = opm.get_paid_states()
        records = Payment.search(domain)
        settlement_ids = records.mapped("settlement_id").ids
        paid_map = opm.settlement_paid_map(env, settlement_ids, paid_states=paid_states)

        for pr in records:
            checked += 1
            settle = pr.settlement_id
            if not settle:
                continue
            currency = pr.company_id.currency_id
            precision = currency.rounding or 0.01
            if precision <= 0:
                precision = 0.01
            paid = paid_map.get(settle.id, 0.0)
            # 排除自身（避免自统计）
            if pr.state in paid_states:
                paid -= pr.amount or 0.0
            payable = (settle.amount_total or 0.0) - paid
            amount = pr.amount or 0.0

            if float_compare(amount, payable, precision_rounding=precision) == 1:
                issues.append(
                    {
                        "model": "payment.request",
                        "res_id": pr.id,
                        "message": _(
                            "付款金额(%(amount)s)超过结算单可付余额(%(payable)s)，请降低金额或拆分付款。"
                        )
                        % {"amount": amount, "payable": payable},
                        "refs": {"name": pr.display_name},
                        "suggestions": [
                            {
                                "res_model": "sc.settlement.order",
                                "res_id": settle.id,
                                "display_name": settle.display_name,
                                "reason": _("参考当前关联结算单的可付余额"),
                            }
                        ],
                    }
                )

        return {
            "rule": self.code,
            "title": self.title,
            "severity": self.severity,
            "checked": checked,
            "issues": issues,
        }
