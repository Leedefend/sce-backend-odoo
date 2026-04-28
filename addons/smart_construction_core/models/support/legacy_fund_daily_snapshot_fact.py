# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ScLegacyFundDailySnapshotFact(models.Model):
    _name = "sc.legacy.fund.daily.snapshot.fact"
    _description = "资金日报"
    _order = "snapshot_date desc, id desc"

    legacy_source_table = fields.Char(string="来源表", required=True, index=True)
    legacy_record_id = fields.Char(string="来源记录", required=True, index=True)
    legacy_pid = fields.Char(string="附件编号", index=True)
    source_family = fields.Char(string="来源分类", index=True)
    document_no = fields.Char(string="单号", index=True)
    snapshot_date = fields.Date(string="日期", required=True, index=True)
    legacy_state = fields.Char(string="状态", index=True)
    state_text = fields.Char(string="状态", compute="_compute_business_aliases")
    subject = fields.Char(string="摘要")
    project_id = fields.Many2one("project.project", string="项目", required=True, index=True, ondelete="cascade")
    legacy_project_id = fields.Char(string="项目原编号", index=True)
    legacy_project_name = fields.Char(string="项目原名称")
    source_account_balance_total = fields.Float(string="账面余额合计")
    source_bank_balance_total = fields.Float(string="银行余额合计")
    source_bank_system_difference = fields.Float(string="账实差异")
    account_balance_total = fields.Float(string="账面余额合计", compute="_compute_business_aliases")
    bank_balance_total = fields.Float(string="银行余额合计", compute="_compute_business_aliases")
    bank_system_difference = fields.Float(string="账实差异", compute="_compute_business_aliases")
    note = fields.Text(string="备注")
    import_batch = fields.Char(string="导入批次", required=True, index=True)

    @api.depends(
        "legacy_state",
        "source_account_balance_total",
        "source_bank_balance_total",
        "source_bank_system_difference",
    )
    def _compute_business_aliases(self):
        for record in self:
            record.state_text = record.legacy_state
            record.account_balance_total = record.source_account_balance_total
            record.bank_balance_total = record.source_bank_balance_total
            record.bank_system_difference = record.source_bank_system_difference
