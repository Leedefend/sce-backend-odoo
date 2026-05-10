# -*- coding: utf-8 -*-
from uuid import uuid4

from odoo import api, fields, models


class ScLegacyPaymentResidualFact(models.Model):
    _name = "sc.legacy.payment.residual.fact"
    _description = "Legacy Payment Residual Fact"
    _order = "document_date desc, source_table, legacy_record_id"

    source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    residual_reason = fields.Char(index=True)
    payment_family = fields.Char(index=True)
    document_no = fields.Char(index=True)
    document_date = fields.Date(index=True)
    document_state = fields.Char(index=True)
    deleted_flag = fields.Char(index=True)
    project_legacy_id = fields.Char(index=True)
    project_name = fields.Char(index=True)
    project_id = fields.Many2one("project.project", index=True, ondelete="set null")
    partner_legacy_id = fields.Char(index=True)
    partner_name = fields.Char(index=True)
    partner_id = fields.Many2one("res.partner", index=True, ondelete="set null")
    contract_legacy_id = fields.Char(index=True)
    contract_no = fields.Char(index=True)
    request_legacy_id = fields.Char(index=True)
    planned_amount = fields.Float()
    paid_amount = fields.Float()
    invoice_amount = fields.Float()
    payment_method = fields.Char(index=True)
    bank_account = fields.Char(index=True)
    handler_name = fields.Char(index=True)
    creator_legacy_user_id = fields.Char(index=True)
    creator_name = fields.Char(index=True)
    created_time = fields.Datetime(index=True)
    attachment_ref = fields.Char()
    note = fields.Text()
    active = fields.Boolean(default=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            context = self.env.context or {}
            payment_family = vals.get("payment_family") or context.get("default_payment_family")
            if payment_family:
                vals["payment_family"] = payment_family
            if not vals.get("source_table"):
                vals["source_table"] = context.get("default_source_table") or "USER_ENTRY"
            if not vals.get("legacy_record_id"):
                vals["legacy_record_id"] = context.get("default_legacy_record_id") or "USER-%s" % uuid4().hex
        return super().create(vals_list)

    _sql_constraints = [
        (
            "legacy_payment_residual_unique",
            "unique(source_table, legacy_record_id)",
            "Legacy payment residual source record must be unique.",
        ),
    ]
