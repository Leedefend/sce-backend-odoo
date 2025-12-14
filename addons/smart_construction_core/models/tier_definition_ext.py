# -*- coding: utf-8 -*-
from odoo import models


class TierDefinition(models.Model):
    _inherit = "tier.definition"

    def _get_tier_validation_model_names(self):
        """扩展 OCA 白名单：加入 project.material.plan"""
        names = super()._get_tier_validation_model_names()
        if not names:
            names = []
        elif isinstance(names, (set, tuple)):
            names = list(names)
        if "project.material.plan" not in names:
            names.append("project.material.plan")
        return names
