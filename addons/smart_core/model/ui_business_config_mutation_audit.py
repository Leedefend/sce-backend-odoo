# -*- coding: utf-8 -*-
from __future__ import annotations

from odoo import fields, models
from odoo.addons.smart_core.utils.business_config_mutation_audit import record_business_config_mutation


class UIBusinessConfigMutationAudit(models.Model):
    _name = "ui.business.config.mutation.audit"
    _description = "UI Business Config Mutation Audit"
    _order = "id desc"

    operation = fields.Selection([("create", "Create"), ("write", "Write"), ("unlink", "Unlink")], required=True, index=True)
    target_model = fields.Char(required=True, index=True)
    target_res_id = fields.Integer(index=True)
    trace_id = fields.Char(index=True)
    value_hash = fields.Char(required=True)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user, readonly=True)
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company, readonly=True)
