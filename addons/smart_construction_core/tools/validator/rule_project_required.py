# -*- coding: utf-8 -*-
from odoo import _

from .rules import DataRule, register


@register
class ProjectRequiredRule(DataRule):
    name = "project_required"
    level = "warn"
    description = "关键单据必须挂项目"

    def run(self):
        env = self.env
        issues = []
        checked = 0
        targets = [
            ("payment.request", "付款/收款申请缺少项目"),
            ("sc.settlement.order", "结算单缺少项目"),
            ("purchase.order", "采购订单缺少项目"),
        ]
        for model, msg in targets:
            Model = env[model].sudo()
            for rec in Model.search([]):
                checked += 1
                if not rec.project_id:
                    issues.append(
                        {
                            "model": model,
                            "res_id": rec.id,
                            "message": _(msg),
                        }
                    )
        return {
            "rule": self.name,
            "level": self.level,
            "checked": checked,
            "issues": issues,
        }
