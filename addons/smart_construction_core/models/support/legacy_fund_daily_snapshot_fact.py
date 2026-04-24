# -*- coding: utf-8 -*-
from odoo import fields, models


class ScLegacyFundDailySnapshotFact(models.Model):
    _name = "sc.legacy.fund.daily.snapshot.fact"
    _description = "Legacy Fund Daily Snapshot Fact"
    _order = "snapshot_date desc, id desc"

    legacy_source_table = fields.Char(required=True, index=True)
    legacy_record_id = fields.Char(required=True, index=True)
    legacy_pid = fields.Char(index=True)
    source_family = fields.Char(index=True)
    document_no = fields.Char(index=True)
    snapshot_date = fields.Date(required=True, index=True)
    legacy_state = fields.Char(index=True)
    subject = fields.Char()
    project_id = fields.Many2one("project.project", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(index=True)
    legacy_project_name = fields.Char()
    source_account_balance_total = fields.Float()
    source_bank_balance_total = fields.Float()
    source_bank_system_difference = fields.Float()
    note = fields.Text()
    import_batch = fields.Char(required=True, index=True)
