# -*- coding: utf-8 -*-
from odoo import _

from .rules import DataRule, register


@register
class AmountQtySanityRule(DataRule):
    name = "amount_qty_sanity"
    level = "warn"
    description = "金额与数量的合理性检查（不允许负数）"

    def run(self):
        env = self.env
        issues = []
        checked = 0

        checks = [
            ("sc.settlement.order.line", "qty", _("结算行数量为负数")),
            ("sc.settlement.order.line", "amount", _("结算行金额为负数")),
            ("payment.request", "amount", _("付款申请金额为负数")),
            ("purchase.order.line", "product_qty", _("采购行数量为负数")),
            ("purchase.order.line", "price_subtotal", _("采购行金额为负数")),
        ]
        for model, field_name, msg in checks:
            Model = env[model].sudo()
            for rec in Model.search([]):
                checked += 1
                val = getattr(rec, field_name, 0.0) or 0.0
                if val < 0:
                    issues.append(
                        {
                            "model": model,
                            "res_id": rec.id,
                            "message": msg,
                        }
                    )

        return {
            "rule": self.name,
            "level": self.level,
            "checked": checked,
            "issues": issues,
        }
