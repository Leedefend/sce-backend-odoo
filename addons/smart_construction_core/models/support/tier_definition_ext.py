# -*- coding: utf-8 -*-
from odoo import models


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    def _get_tier_validation_model_names(self):
        """扩展 OCA 白名单：加入业务审批执行模型。"""
        names = super()._get_tier_validation_model_names()
        if not names:
            names = []
        elif isinstance(names, (set, tuple)):
            names = list(names)
        for model_name in [
            "project.material.plan",
            "payment.request",
            "sc.expense.claim",
            "sc.settlement.order",
            "purchase.order",
            "construction.contract",
            "sc.general.contract",
            "sc.legacy.purchase.contract.fact",
        ]:
            if model_name not in names:
                names.append(model_name)
        return names
