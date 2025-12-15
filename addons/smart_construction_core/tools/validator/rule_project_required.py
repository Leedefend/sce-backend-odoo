# -*- coding: utf-8 -*-
from odoo import _

from .rules import BaseRule, register, SEVERITY_WARN


@register
class ProjectRequiredRule(BaseRule):
    code = "SC.VAL.PROJ.001"
    title = "关键单据必须挂项目"
    severity = SEVERITY_WARN

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
            "rule": self.code,
            "title": self.title,
            "severity": self.severity,
            "checked": checked,
            "issues": issues,
        }
